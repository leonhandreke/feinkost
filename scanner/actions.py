from datetime import datetime, timedelta

from feinkost.models import InventoryItem
from scanner.exceptions import InvalidOperationError


class ActionManager():
    previous_actions = []

    def execute_action(self, action):
        self.previous_actions.append(action)
        action.execute()

    def get_previous_action(self):
        try:
            return self.previous_actions[-1]
        except IndexError:
            raise InvalidOperationError("No previous item to set the quantity of!")

    def undo_previous_action(self):
        if not self.previous_actions:
            raise InvalidOperationError("No previous action to undo.")
        a = self.previous_actions.pop()
        a.undo()
        return a


class ActionBase():
    def set_quantity(self):
        raise InvalidOperationError("Set quantity not possible on " + self.__class__)

    def set_quantity_state(self):
        raise InvalidOperationError("Set quantity not possible on " + self.__class__)


class InventoryItemActionBase(ActionBase):
    def set_quantity(self, times):
        self.inventory_item.quantity_state = None
        self.inventory_item.quantity = times
        self.inventory_item.save()

    def set_quantity_state(self, quantity_state):
        self.inventory_item.quantity = None
        self.inventory_item.quantity_state = quantity_state
        self.inventory_item.save()


class InventoryItemAddAction(InventoryItemActionBase):
    def __init__(self, product):
        self.product = product

    def execute(self):
        if self.product.best_before_days:
            best_before = datetime.now() + timedelta(days=self.product.best_before_days)
        else:
            best_before = None
        self.inventory_item = InventoryItem(
            product=self.product,
            best_before=best_before,
            quantity=1.0).save()

    def undo(self):
        self.inventory_item.delete()

    def __str__(self):
        quantity = (self.inventory_item.quantity or
                    self.inventory_item.quantity_state.display_name)
        return 'Add %s %s %s%s' % (quantity, self.product.name,
                                   self.product.quantity, self.product.get_unit())


class InventoryItemModifyAction(InventoryItemActionBase):
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
