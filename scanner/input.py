from decimal import Decimal, InvalidOperation
import re
import readline

import click

from feinkost.models import ProductCategory


TRADING_UNIT_RE = '(\d+\.?\d*)([a-zA-Z]*)'


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
