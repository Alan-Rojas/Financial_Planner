class Income():
    def __init__(self, name: str, amount: int, recurrence: int, inc: bool = False, increment_rate: float = 0.0):
        """
        :param name: name of the income (maybe 'Salary', 'Rent', 'Sales')
        :param amount: current amount of the income
        :param recurrence: recurrence in months (so 1 = monthly, 12 = yearly)
        :param inc: whether the income increases over time. By default set to false
        :param increment_rate: rate of increase (say 0.05 is 5%)
        """
        self.name = name
        self.amount = amount
        self.recurrence = recurrence
        self.inc = inc
        self.increment_rate = increment_rate if inc else 0.0
        self.active = True

    def receive(self) -> int:
        """Returns the current charge amount"""
        return self.amount if self.active else 0.0

    def apply_increment(self):
        """Increases the income by increment_rate"""
        if self.inc and self.active:
            self.amount *= (1 + self.increment_rate)

    def delete(self):
        """Deactivate the income."""
        self.active = False

    # ---- Properties ----
    @property
    def is_active(self):
        return self.active

    @property
    def monthly_equivalent(self):
        """Return normalized monthly income (for forecasting)."""
        return (self.amount / self.recurrence) if self.active else 0.0

    def __repr__(self): # Useful to have a safety net for debugging
        return (f"Income(name={self.name}, amount={self.amount:.2f}, "
                f"recurrence={self.recurrence}, inc={self.inc}, "
                f"increment_rate={self.increment_rate}, active={self.active})")


