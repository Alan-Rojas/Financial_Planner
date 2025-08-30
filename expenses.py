# This file defines the expenses class
class Expense:
    def __init__(self, name: str, amount: float, recurrence: int, inc: bool = False, increment_rate: float = 0.0):
        """
        :param name: name of the expense (maybe 'Rent', 'Groceries')
        :param amount: current amount of the expense
        :param recurrence: recurrence in months (so 1 = monthly, 12 = yearly)
        :param inc: whether the expense increases over time. By default set to false
        :param increment_rate: rate of increase (say 0.05 is 5%)
        """
        self.name = name
        self.amount = amount
        self.recurrence = recurrence
        self.inc = inc
        self.increment_rate = increment_rate if inc else 0.0
        self.active = True # This will be useful as expenses might become irrelevant for some period of time, so we might as well turn them off

    def charge(self) -> int:
        """Returns the current charge amount"""
        return self.amount if self.active else 0.0

    def apply_increment(self):
        """Increases the expense by increment_rate"""
        if self.inc and self.active:
            self.amount *= (1 + self.increment_rate)

    def delete(self):
        """Deactivate the expense."""
        self.active = False

    # ---- Properties ----
    @property
    def is_active(self):
        return self.active

    @property
    def monthly_equivalent(self):
        """Return normalized monthly cost (for forecasting)."""
        return (self.amount / self.recurrence) if self.active else 0.0

    def __repr__(self): # Useful to have a safety net for debugging
        return (f"Expense(name={self.name}, amount={self.amount:.2f}, "
                f"recurrence={self.recurrence}, inc={self.inc}, "
                f"increment_rate={self.increment_rate}, active={self.active})")


