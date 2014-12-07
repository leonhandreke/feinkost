from decimal import Decimal, InvalidOperation

import click
from click.exceptions import Abort

from feinkost.models import Product, InventoryItem
from feinkost import constants, codecheck

from scanner.actions import execute_action, InventoryItemAddAction, InventoryItemModifyAction
from scanner.input import input_default, input_trading_unit, input_category
from scanner.exceptions import InvalidOperationError


click.echo('Welcome to Feinkost!')

MODE_ADD = 'MODE_ADD'
MODE_REMOVE = 'MODE_REMOVE'

current_mode = MODE_ADD

previous_actions = []


def convert_to_database_unit(quantity, unit):
    try:
        unit, conversion = next(((k[1], v) for (k, v) in constants.UNIT_CONVERSIONS.items()
                                 if k[0] == unit and k[1] in constants.DATABASE_UNITS))
    except StopIteration:
        click.echo("No conversion to unit valid in database found")
        return

    quantity = conversion(quantity)
    return quantity, unit


def add_new_product(barcode):
    try:
        codecheck_info = codecheck.get_product_data_by_barcode(barcode)
    except Exception:
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


def add_new_refillable_container(barcode):
    if not barcode.startswith('02'):
        return False

    click.echo("Add new refillable container.")
    capacity, unit = input_trading_unit()
    capacity, unit = convert_to_database_unit(capacity, unit)

    category = input_category(unit)

    if (category.get_unit(), unit) not in constants.UNIT_CONVERSIONS.keys():
        click.echo("Capacity unit is not convertible to category unit!")
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
    if len(v) < 8:
        return

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


def get_previous_action(qty):
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

def set_previous_item_quantity(qty):

    if not hasattr(a, 'set_quantity'):
        click.secho("Cannot set quantity on previous action!", fg='red')
        return

    a.set_quantity(Decimal(qty))
    click.echo(a)
    return


def process_commands(v):
    if v == '02000053':
        set_previous_item_quantity(0.5)
        return True

    if v == 'MADD':
        current_mode = MODE_ADD
        return True

    if v == 'MREM':
        current_mode = MODE_REMOVE
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

    try:
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
        raise InvalidOperationError("No command found!")
    except InvalidOperationError as e:
        click.secho(e, fg='red')

click.echo("Bye!")
