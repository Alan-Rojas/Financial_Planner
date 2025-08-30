class Event:
    def __init__(self, name: str, trigger_month: int, action: callable):
        """
        :param name: descriptive name (e.g. 'Got Married', 'Job Promotion')
        :param trigger_month: when the event should be triggered (e.g. month 24)
        :param action: a function that applies the effect of the event
                       (must accept the FinanceManager or affected objects)
        """
        self.name = name
        self.trigger_month = trigger_month
        self.action = action
        self.executed = False

    def apply(self, month: int, finance_manager):
        """Check if event should trigger and apply its effect."""
        if month == self.trigger_month and not self.executed:
            self.action(finance_manager)
            self.executed = True

    def __repr__(self):
        return f"Event(name={self.name}, trigger_month={self.trigger_month}, executed={self.executed})"
