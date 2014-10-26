from datetime import datetime, timedelta

import click
from click.exceptions import Abort

from feinkost.models import Product, InventoryItem

click.echo('Welcome to Feinkost!')

MODE_ADD = 'MODE_ADD'
MODE_REMOVE = 'MODE_REMOVE'

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
        self.inventory_item = InventoryItem(
            product=self.product,
            best_before=datetime.now() + timedelta(days=self.product.best_before_days),
            quantity=self.product.quantity).save()

    def undo(self):
        self.inventory_item.delete()

    def multiply(self, times):
        self.inventory_item.quantity = self.inventory_item.quantity * times
        self.inventory_item.save()

    def __str__(self):
        return 'Add %s%s %s' % (self.inventory_item.quantity, self.product.get_unit(), self.product.name)


def process_barcode_add(v):
    p = Product.objects.get(barcode=v)
    a = InventoryItemAddAction(p)
    a.execute()
    click.echo(a)
    previous_actions.append(a)
    return True

def process_commands(v):
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
        v = click.prompt('feinkost >')
    except Abort:
        break

    is_integer = True
    try:
        int(v)
    except ValueError:
        is_integer = False

    # Check if this is a barcode
    if is_integer and len(v) >= 10:
        if current_mode is MODE_ADD:
            if process_barcode_add(v):
                continue

    if is_integer and len(v) < 3:
        a = previous_actions[-1]
        if not hasattr(a, 'multiply'):
            click.echo("Cannot multiply previous action")
            continue
        a.multiply(int(v))
        click.echo(a)
        continue

    if process_commands(v):
        continue

    click.secho('Invalid input!', fg='red')

click.echo("Bye!")
