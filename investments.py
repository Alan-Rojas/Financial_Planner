from incomes import *
import numpy as np

class Investment():
    def __init__(self, name: str, amount: float, yearly_return_rate: float, volatility: float, dividend_per: float):
        """
        :param name: name of the income (maybe 'Stocks', 'ETF's', 'Crypt')
        :param amount: current amount of the income
        :param recurrence: recurrence in months (so 1 = monthly, 12 = yearly)
        :param inc: whether the income increases over time. By default set to false
        :param increment_rate: rate of increase (say 0.05 is 5%)
        """
        self.name = name
        self.amount = amount
        self.strt_amount = amount
        self.yearly_return_rate = yearly_return_rate
        self.volatility = volatility
        self.dividend_per = dividend_per
        self.active = True

    def add_funds(self, add_amount):
        if self.active: 
            self.amount += add_amount 
    
    def revaluation(self):
        if self.active:

            if self.volatility > np.random.rand():
                # This means that a random event will happen, either a drop or a rise
                dir = 1 if np.random.rand() > 0.5 else -1 # 
                rate = np.random.choice(a = [0.05, 0.1, 0.15, 0.2, 0.3], p = [0.6, 0.2, 0.125, 0.05, 0.025]) 
                self.amount *= abs(dir + rate) 
        

    def yearly_increase(self):
        if self.active:
            self.amount *= (1 + self.yearly_return_rate)
    
    def dividend(self):
        return self.amount * self.dividend_per if self.active else False

    def delete(self):
        self.active = False

    @property
    def is_active(self):
        return self.active
    
    def __repr__(self): # Useful to have a safety net for debugging
        return (f"Investment(name={self.name}, amount={self.amount:.2f}, "
                f"return_rate={self.yearly_return_rate}, volatility={self.volatility}, "
                f"dividend_per={self.dividend_per}, active={self.active})")

