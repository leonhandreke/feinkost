import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import readline

import click
from click.exceptions import Abort

from feinkost.models import Product, InventoryItem, ProductCategory
from feinkost import constants, codecheck

click.echo('Welcome to Feinkost!')

MODE_ADD = 'MODE_ADD'
MODE_REMOVE = 'MODE_REMOVE'

TRADING_UNIT_RE = '(\d+\.?\d*)([a-zA-Z]*)'

current_mode = MODE_ADD

previous_actions = []

class ModeSwitchAction():
    def __init__(self, mode):
        self.previous_mode = current_mode
        self.mode = mode

    def execute(self):
        current_mode = self.mode

    def undo(self):
        current_mode = self.previous_mode

    def __str__(self):
        return 'Switch to ' + self.mode


class InventoryItemAddAction():
    def __init__(self, product):
        self.product = product

    def execute(self):
        if self.product.best_before_days:
            best_before = datetime.now() + timedelta(days=self.product.best_before_days),
        else:
            best_before = None
        self.inventory_item = InventoryItem(
            product=self.product,
            best_before=best_before,
            quantity=1.0).save()

    def undo(self):
        self.inventory_item.delete()

    def set_quantity(self, times):
        self.inventory_item.quantity = times
        self.inventory_item.save()

    def __str__(self):
        return 'Add %s %s %s%s' % (self.inventory_item.quantity, self.product.name,
                                   self.product.quantity, self.product.get_unit())


class InventoryItemModifyAction():
    def __init__(self, inventory_item):
        self.inventory_item = inventory_item

    def execute(self):
        pass

    def set_quantity(self, times):
        self.inventory_item.quantity = times
        self.inventory_item.save()

    def __str__(self):
        return 'Modify %s %s x %s%s' % (self.inventory_item.get_display_name(),
                                        self.inventory_item.quantity,
                                        self.inventory_item.capacity,
                                        self.inventory_item.get_unit())


def input_default(text, startup_text=''):
    readline.set_startup_hook(lambda: readline.insert_text(startup_text))
    r = input(text + ': ')
    readline.set_startup_hook(None)
    return r

def input_trading_unit(default_text=''):
    try:
        trading_unit = input_default('Trading Unit', default_text)
    except EOFError:
        return

    match = re.match(TRADING_UNIT_RE, trading_unit)

    try:
        quantity = Decimal(match.group(1))
    except InvalidOperation:
        click.echo("Invalid trading unit.")
        return

    unit = match.group(2)

    return (quantity, unit)

def convert_to_database_unit(quantity, unit):
    try:
        unit, conversion = next(((k[1],v) for (k,v) in constants.UNIT_CONVERSIONS.items() if k[0] == unit))
    except StopIteration:
        click.echo("No conversion to unit valid in database found")
        return

    quantity = conversion(quantity)
    return quantity, unit

def add_new_product(barcode):
    try:
        codecheck_info = codecheck.get_product_data_by_barcode(barcode)
    except Exception as e:
        click.echo("Failed to get product information from codecheck.info")
        codecheck_info = {
            'name': '',
            'category': '',
            'unit': '',
            'quantity': ''
        }

    try:
        name = input_default('Name', codecheck_info['name'])
        quantity, unit = input_trading_unit(str(codecheck_info['quantity']) + codecheck_info['unit'])
    except EOFError:
        return

    quantity, unit = convert_to_database_unit(quantity, unit)

    category = input_category(unit, codecheck_info['category'])
    if not category:
        return

    try:
        best_before_days = input_default('Best Before Days')
    except EOFError:
        return

    if not best_before_days:
        best_before_days = None

    p = Product(barcode=barcode, name=name,
            quantity=quantity, best_before_days=best_before_days,
            category=category)
    p.save()
    return p

def input_category(unit, default_text=''):
    try:
        category_name = input_default('Category', default_text)
    except EOFError:
        return

    try:
        return ProductCategory.objects.get(name=category_name)
    except ProductCategory.DoesNotExist:
        if click.confirm("Product category %s does not exist. Create?" % category_name, default=True):
            return ProductCategory(name=category_name, unit=unit).save()
        else:
            return

def add_new_refillable_container(barcode):
    if not barcode.startswith('02'):
        return False

    click.echo("Add new refillable container.")
    capacity, unit = input_trading_unit()
    capacity, unit = convert_to_database_unit(capacity, unit)

    category = input_category(unit)

    if unit != category.get_unit():
        click.echo("Capacity unit does not match category unit!")
        return True

    i = InventoryItem(barcode=barcode,
                      capacity=capacity,
                      category=category,
                      quantity=1.0)
    i.save()
    # Allow modification right afterwards
    a = InventoryItemModifyAction(i)
    previous_actions.append(a)
    click.echo(a)
    return i


def process_barcode_add(v):
    try:
        p = Product.objects.get(barcode=v)
    except Product.DoesNotExist:
        if click.confirm("Product with barcode %s does not exist! Create?" % v, default=True):
            p = add_new_product(barcode=v)
        else:
            return

    if not p:
        return

    a = InventoryItemAddAction(p)
    a.execute()
    click.echo(a)
    previous_actions.append(a)
    return True


def process_barcode_inventory_item_modify(v):
    """Process barcodes attached to refillable containers."""
    try:
        i = InventoryItem.objects.get(barcode=v)
    except InventoryItem.DoesNotExist:
        return

    a = InventoryItemModifyAction(i)
    previous_actions.append(a)
    click.echo(a)
    return True

def set_previous_item_quantity(qty):
    try:
        a = previous_actions[-1]
    except IndexError:
        click.secho("No previous item to set the quantity of!", fg='red')
        return

    if not hasattr(a, 'set_quantity'):
        click.secho("Cannot set quantity on previous action!", fg='red')
        return

    a.set_quantity(Decimal(qty))
    click.echo(a)
    return

def process_commands(v):
    if v =='02000053':
        set_previous_item_quantity(0.5)
        return True

    if v == 'MADD':
        a = ModeSwitchAction(MODE_ADD)
        a.execute()
        click.echo(a)
        previous_actions.append(a)
        return True

    if v == 'MREM':
        a = ModeSwitchAction(MODE_REMOVE)
        a.execute()
        click.echo(a)
        previous_actions.append(a)
        return True

    if v == 'UNDO':
        a = previous_actions.pop()
        a.undo()
        click.echo('Undo "%s"' % a)
        return True

while True:
    # TODO: Read directly from the input device
    try:
        v = click.prompt('feinkost >', prompt_suffix='')
    except Abort:
        break

    if process_commands(v):
        continue

    if process_barcode_inventory_item_modify(v):
        continue

    if add_new_refillable_container(v):
        continue

    if MODE_ADD:
        if process_barcode_add(v):
            continue

    try:
        f = Decimal(v)
        a = previous_actions[-1]
        if not hasattr(a, 'set_quantity'):
            click.echo("Cannot set quantity of previous action")
            continue
        a.set_quantity(f)
        click.echo(a)
        continue
    except InvalidOperation:
        pass

    click.secho('Invalid input!', fg='red')

click.echo("Bye!")
