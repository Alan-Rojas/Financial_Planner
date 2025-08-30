class Target:
    def __init__(self, name: str, check_function: callable, goal_value: float):
        """
        :param name: descriptive goal name (e.g. 'Monthly Income Goal')
        :param check_function: function that computes the current value (takes FinanceManager)
        :param goal_value: the threshold that must be reached
        """
        self.name = name
        self.check_function = check_function
        self.goal_value = goal_value

    def status(self, finance_manager):
        """Return current value and progress %."""
        current_value = self.check_function(finance_manager)
        progress = min(100, (current_value / self.goal_value) * 100)
        return current_value, progress

    def is_reached(self, finance_manager) -> bool:
        """Check if the goal is met."""
        current_value, _ = self.status(finance_manager)
        return current_value >= self.goal_value

    def __repr__(self):
        return f"Target(name={self.name}, goal={self.goal_value})"
