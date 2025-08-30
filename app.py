import streamlit as st
from finance_manager import *  

# For some reason Streamlit kept erasing the Fm objects
if 'fm' not in st.session_state:
    st.session_state.fm = FinanceManager(starting_cash=15000, reinvest_dividends=False, 
                                         invest_sweep_rate=0.60, allocation={"Stocks": 0.6, "Crypto": 0.4}, random_seed=42)


fm = st.session_state.fm

# --- Page Beginning ---
st.title('Personal Finance Simulator')

st.sidebar.header('Simulation Controls')

run_simulation = st.sidebar.button('Run Simulation')

months = st.sidebar.number_input('Number of months to run', min_value=1, value=120)

# --- Main Page --- 

st.header("Configure Your Financial Plan")

# --- Incomes ---
with st.expander("Add Income"):
    income_name = st.text_input('Income Name', key="income_name")
    income_amount = st.number_input('Income Amount', min_value=1, value=20000)
    income_recurrence = st.number_input('Income Recurrence (in months)', min_value=1, value=1)
    add_income = st.button('Add Income', key="add_income")

    if add_income:
        income = Income(income_name, income_amount, income_recurrence)
        fm.add_income(income)
        st.success(f'Income "{income_name}" added!')

# --- Expenses ---
with st.expander("Add Expense"):
    expense_name = st.text_input('Expense Name', key="expense_name")
    expense_amount = st.number_input('Expense Amount', min_value=1, value=6000)
    expense_recurrence = st.number_input('Expense Recurrence (in months)', min_value=1, value=1)
    add_expense = st.button('Add Expense', key="add_expense")

    if add_expense:
        expense = Expense(expense_name, expense_amount, expense_recurrence)
        fm.add_expense(expense)
        st.success(f'Expense "{expense_name}" added!')

# --- Investments ---
with st.expander("Add Investment"):
    investment_name = st.text_input('Investment Name', key="investment_name")
    investment_amount = st.number_input('Investment Amount', min_value=1, value=30000)
    investment_return = st.number_input('Investment Yearly Return Rate', min_value=0.0, value=0.20)
    investment_volatility = st.number_input('Investment Volatility Rate', min_value=0.0, value=0.1)
    investment_dividend = st.number_input('Investment Dividend Rate', min_value=0.0, value=0.0002)
    add_investment = st.button('Add Investment', key="add_investment")

    if add_investment:
        investment = Investment(investment_name, investment_amount, investment_return, investment_volatility, investment_dividend)
        fm.add_investment(investment)
        st.success(f'Investment "{investment_name}" added!')

# --- Events ---
with st.expander("Add Event"):
    event_name = st.text_input('Event Name', key="event_name")
    event_trigger_month = st.number_input('Event Trigger Month', min_value=1, value=12)
    event_obj_type = st.selectbox("Object Type", ["Income", "Expense", "Investment"], key="event_obj_type")
    event_obj_name = st.text_input('Object Name', key="event_obj_name")
    operation = st.selectbox("Operation", ["add", "multiply", "reduce_percent", "add_percent"], key="event_operation")
    event_value = st.number_input('Value for Operation', min_value=0.0, value=0.05)
    add_event = st.button('Add Event', key="add_event")

    if add_event:
        action = make_event_action(event_obj_type, event_obj_name, operation, event_value)
        add_event_to_fm(fm, event_name, event_trigger_month, action)
        st.success(f'Event "{event_name}" added!')

# --- Targets ---
with st.expander("Add Target"):
    target_name = st.text_input('Target Name', key="target_name")
    target_goal_value = st.number_input('Target Goal Value', min_value=0.0, value=300000.00)
    add_target = st.button('Add Target', key="add_target")

    if add_target:
        add_target_to_fm(fm, target_name, lambda f: f.total_monthly_income_equivalent(), target_goal_value)
        st.success(f'Target "{target_name}" added!')

# We gonna be able to see all the setup by object
st.header("Current Financial Setup")

# Display added Incomes
st.subheader("Incomes")
for income in fm.incomes:
    st.write(f"Name: {income.name}, Amount: {income.amount}, Recurrence: {income.recurrence} months")

# Display added Expenses
st.subheader("Expenses")
for expense in fm.expenses:
    st.write(f"Name: {expense.name}, Amount: {expense.amount}, Recurrence: {expense.recurrence} months")

# Display added Investments
st.subheader("Investments")
for investment in fm.investments:
    st.write(f"Name: {investment.name}, Amount: {investment.amount}, Yearly Return Rate: {investment.yearly_return_rate}")

# Display added Events
st.subheader("Events")
for event in fm.events:
    st.write(f"Name: {event.name}, Trigger Month: {event.trigger_month}")

# Display added Targets
st.subheader("Targets")
for target in fm.targets:
    st.write(f"Name: {target.name}, Goal Value: {target.goal_value}")

# --- Running ---
if run_simulation:
    results = fm.run(months)

    for target in fm.targets:
        fig = plot_target_progress(fm, target.name)
        st.pyplot(fig)
