from typing import List, Callable, Dict, Optional, Tuple
import numpy as np
from events import Event
from expenses import Expense
from incomes import Income
from investments import Investment
from targets import Target
import matplotlib.pyplot as plt

class FinanceManager:
    def __init__(
        self,
        start_month: int = 0,
        starting_cash: float = 0.0,
        reinvest_dividends: bool = True,
        invest_sweep_rate: float = 0.0,
        allocation: Optional[Dict[str, float]] = None,
        random_seed: Optional[int] = None,
    ):
        """
        :param start_month: starting month index (0-based)
        :param starting_cash: initial cash balance
        :param reinvest_dividends: if True, dividends auto-reinvest into each investment
        :param invest_sweep_rate: fraction of end-of-month cash to auto-invest (0..1)
        :param allocation: dict mapping investment.name -> fraction of the sweep (must sum to 1.0 if provided)
        :param random_seed: set for reproducible stochastic revaluation
        """
        self.month = start_month
        self.cash = float(starting_cash)

        self.incomes: List[Income] = []
        self.expenses: List[Expense] = []
        self.investments: List[Investment] = []
        self.events: List[Event] = []
        self.targets: List[Target] = []

        self.reinvest_dividends = reinvest_dividends
        self.invest_sweep_rate = invest_sweep_rate
        self.allocation = allocation or {}

        self.history: List[dict] = []

        if random_seed is not None:
            np.random.seed(random_seed)

    # ---------------- Adders ----------------

    def add_income(self, income: Income):
        self._validate_recurrence(income.recurrence, "Income")
        self.incomes.append(income)

    def add_expense(self, expense: Expense):
        self._validate_recurrence(expense.recurrence, "Expense")
        self.expenses.append(expense)

    def add_investment(self, investment: Investment):
        self.investments.append(investment)

    def add_event(self, event: Event):
        self.events.append(event)

    def add_target(self, target: Target):
        self.targets.append(target)

    # ---------------- Helpers ----------------

    @staticmethod
    def _validate_recurrence(recurrence: int, kind: str):
        if not isinstance(recurrence, int) or recurrence < 1:
            raise ValueError(f"{kind}.recurrence must be an integer >= 1")

    def _is_due(self, obj) -> bool:
        """True if an Income/Expense is due this month based on its recurrence."""
        # Example rule: due in month 0, recurrence, 2*recurrence, ...
        return obj.is_active and (self.month % obj.recurrence == 0)

    def _apply_increments_if_cycle_end(self):
        """
        For each due income/expense this month, apply its increment AFTER charging/receiving.
        Rationale: the new rate applies starting next cycle.
        """
        for inc in self.incomes:
            if self._is_due(inc) and inc.inc:
                inc.apply_increment()
        for exp in self.expenses:
            if self._is_due(exp) and exp.inc:
                exp.apply_increment()

    # ---------------- Aggregates (used by Targets) ----------------

    def total_monthly_income_equivalent(self) -> float:
        div = sum((inv.dividend() / 12.0) for inv in self.investments if inv.is_active) if not self.reinvest_dividends else 0
        inc = sum(i.monthly_equivalent for i in self.incomes if i.is_active)
        return div + inc

    def total_monthly_expense_equivalent(self) -> float:
        return sum(e.monthly_equivalent for e in self.expenses if e.is_active)

    def total_investments(self) -> float:
        return sum(inv.amount for inv in self.investments if inv.is_active)

    def total_dividends_monthly_equivalent(self) -> float:
        # dividends are defined yearly in Investment; normalize to monthly
        return sum((inv.dividend() / 12.0) for inv in self.investments if inv.is_active)

    # ---------------- Month step ----------------

    def step_month(self) -> dict:
        """
        Advance the simulation by one month:
        1) Trigger events scheduled for this month
        2) Process due incomes/expenses (cash in/out)
        3) Apply dividends (reinvest or add to cash)
        4) Apply investment revaluation (volatility)
        5) Apply yearly expected growth on month 12, 24, 36, ...
        6) Auto-invest a sweep of cash according to allocation
        7) Apply increments to incomes/expenses due this month
        8) Record snapshot and increment month
        """
        # 1) Events
        for ev in self.events:
            ev.apply(self.month, self)

        # 2) Incomes & Expenses due this month
        income_this_month = 0.0
        for inc in self.incomes:
            if self._is_due(inc):
                amt = inc.receive()
                income_this_month += amt
                self.cash += amt

        expense_this_month = 0.0
        for exp in self.expenses:
            if self._is_due(exp):
                amt = exp.charge()
                expense_this_month += amt
                self.cash -= amt

        # 3) Dividends (monthly equivalent)
        dividends_received = 0.0
        for inv in self.investments:
            if inv.is_active:
                monthly_div = inv.dividend() / 12.0
                dividends_received += monthly_div
                if self.reinvest_dividends:
                    inv.add_funds(monthly_div)
                else:
                    self.cash += monthly_div

        # 4) Investment revaluation (stochastic volatility event)
        for inv in self.investments:
            inv.revaluation()

        # 5) Apply yearly expected growth at year-end boundaries
        if (self.month + 1) % 12 == 0:
            for inv in self.investments:
                inv.yearly_increase()

        # 6) Auto-invest a sweep of available cash (optional)
        invested_from_sweep = 0.0
        if self.invest_sweep_rate > 0 and self.allocation:
            sweep_amount = max(0.0, self.cash * self.invest_sweep_rate)
            if sweep_amount > 0:
                total_alloc = sum(self.allocation.values())
                if total_alloc <= 0:
                    raise ValueError("Allocation must have positive weights.")
                for name, weight in self.allocation.items():
                    target = next((inv for inv in self.investments if inv.name == name and inv.is_active), None)
                    if target is None:
                        continue
                    add_amt = sweep_amount * (weight / total_alloc)
                    target.add_funds(add_amt)
                    invested_from_sweep += add_amt
                self.cash -= invested_from_sweep

        # 7) Apply increments (after this month’s charge/receive)
        self._apply_increments_if_cycle_end()

        # 8) Collect snapshot & advance time
        total_investments_value = self.total_investments()
        snapshot = {
            "month": self.month,
            "cash": round(self.cash, 2),
            "income": round(income_this_month, 2),
            "expense": round(expense_this_month, 2),
            "dividends": round(dividends_received, 2),
            "invested": round(invested_from_sweep, 2),
            "investments_total": round(total_investments_value, 2),
            "targets": self._targets_status(),  # Capture target status here
        }
        self.history.append(snapshot)  # Save snapshot to history
        self.month += 1
        return snapshot

    def run(self, months: int) -> List[dict]:
        """Run the simulation for a number of months; returns list of monthly snapshots."""
        results = []
        for _ in range(months):
            snapshot = self.step_month()
            results.append(snapshot)
        return results

    # ---------------- Targets ----------------

    def _targets_status(self) -> List[Tuple[str, float, float, bool]]:  
        """
        Returns per-target status tuples:
        (target_name, current_value, progress_percent, reached_bool)
        """
        statuses = []
        for t in self.targets:
            current, progress = t.status(self)  # Assume this method works correctly
            statuses.append((t.name, current, progress, t.is_reached(self)))
        return statuses

    # ---------------- Convenience API (used by events/actions) ----------------

    def get_income(self, name: str) -> Optional["Income"]:
        return next((i for i in self.incomes if i.name == name and i.is_active), None)

    def get_expense(self, name: str) -> Optional["Expense"]:
        return next((e for e in self.expenses if e.name == name and e.is_active), None)

    def get_investment(self, name: str) -> Optional["Investment"]:
        return next((v for v in self.investments if v.name == name and v.is_active), None)
    
    def get_object(self, obj_type: str, obj_name: str):
        """
        Retrieve an object (income, expense, investment, event, target) by type and name.

        :param obj_type: one of ["income", "expense", "investment", "event", "target"]
        :param obj_name: the name of the object to retrieve
        :return: the object instance if found, else None
        """
        obj_type = obj_type.lower()

        mapping = {
            "income": self.incomes,
            "expense": self.expenses,
            "investment": self.investments,
            "event": self.events,
            "target": self.targets,
        }

        if obj_type not in mapping:
            raise ValueError(f"Unknown obj_type '{obj_type}'. Must be one of {list(mapping.keys())}")

        # Events and Targets don’t necessarily have is_active; filter only where relevant
        collection = mapping[obj_type]
        for obj in collection:
            if getattr(obj, "name", None) == obj_name:
                if hasattr(obj, "is_active") and not obj.is_active:
                    continue
                return obj
        return None

    def delete_object(self, obj_type: str, obj_name: str) -> bool:
        """
        Delete (or deactivate) an object from the manager by type and name.

        :param obj_type: one of ["income", "expense", "investment", "event", "target"]
        :param obj_name: the name of the object to delete
        :return: True if object was found and removed/deactivated, False otherwise
        """
        obj_type = obj_type.lower()

        mapping = {
            "income": self.incomes,
            "expense": self.expenses,
            "investment": self.investments,
            "event": self.events,
            "target": self.targets,
        }

        if obj_type not in mapping:
            raise ValueError(f"Unknown obj_type '{obj_type}'. Must be one of {list(mapping.keys())}")

        collection = mapping[obj_type]

        for i, obj in enumerate(collection):
            if getattr(obj, "name", None) == obj_name:
                # For things with is_active, just deactivate
                if hasattr(obj, "is_active"):
                    obj.is_active = False
                else:
                    # For events/targets, actually remove from list
                    collection.pop(i)
                return True

        return False

# ------- Helper functions to mantain modularity in the APP

def plot_target_progress(finance_manager: FinanceManager, target_name: str):
    """
    Plot how a given target has progressed over the simulation.
    
    :param finance_manager: FinanceManager object (with .history filled by run())
    :param target_name: the name of the target to plot
    :return: the plot object to be rendered in Streamlit
    """
    months = []
    values = []
    goal_value = None

    print(f"Available targets: {[t.name for t in finance_manager.targets]}")  # Debugging line

    for snap in finance_manager.history:
        months.append(snap["month"])
        for t_name, current, progress, reached in snap["targets"]:
            if t_name == target_name:
                values.append(current)
                # fetch static goal value from fm.targets (only once)
                if goal_value is None:
                    goal_value = next(
                        t.goal_value for t in finance_manager.targets if t.name == target_name
                    )

    if not values:
        raise ValueError(f"No target named '{target_name}' found in history.")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(months, values, label=f"Progress: {target_name}")
    ax.axhline(y=goal_value, color="red", linestyle="--", label="Goal")
    ax.set_xlabel("Month")
    ax.set_ylabel("Value")
    ax.set_title(f"Target Progress: {target_name}")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)

    return fig # Streamlit likes the figures returned

def add_income_to_fm(fm, name: str, amount: float, frequency: int, inc=False, increment_rate=0.0):
    income = Income(name, amount, frequency, inc, increment_rate)
    fm.add_income(income)

def add_expense_to_fm(fm, name: str, amount: float, frequency: int, inc=False, increment_rate=0.0):
    expense = Expense(name, amount, frequency, inc, increment_rate)
    fm.add_expense(expense)

def add_investment_to_fm(fm, name: str, starting_amount: float, yearly_return_rate: float, volatility: float, dividend_per: float):
    inv = Investment(name, starting_amount, yearly_return_rate, volatility, dividend_per)
    fm.add_investment(inv)

def add_target_to_fm(fm, name: str, eval_func: callable, target_value: float):
    target = Target(name, eval_func, target_value)
    fm.add_target(target)
    print(f"Added target: {target.name}")  # Debugging line to ensure the target is added

def add_event_to_fm(fm, name: str, trigger_month: int, action: callable):
    event = Event(name, trigger_month, action)
    fm.add_event(event)

def make_event_action(obj_type, obj_name: str, operation: str, value: float):
    
    def action(fm):
        obj = fm.get_object(obj_type, obj_name)
        if operation == "add":
            obj.amount += value
        elif operation == "multiply":
            obj.amount *= value
        elif operation == "reduce_percent":
            obj.amount *= (1 - value)
        elif operation == "add_percent":
            obj.amount *= (1 + value)

    return action
