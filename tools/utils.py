# === TOOLS SETUP ===
def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
    """
    return a * b

# This will be a tool
def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b

def divide(a: int, b: int) -> float:
    """Divide a and b.

    Args:
        a: first int
        b: second int
    """
    return a / b

from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

from tools.schemas import Expense, Income, Budget
from tools.db import save_expense, get_expenses, get_latest_budget

@tool
def add_expense(amount: float, category: str, description: str, date: Optional[str] = None) -> str:
    """
    Add a new expense to the database.
    
    Args:
        amount: Amount of the expense
        category: Category of the expense (e.g., 'food', 'housing', 'transportation')
        description: Description of the expense
        date: Date of the expense in ISO format (YYYY-MM-DD). Defaults to today if not provided.
    """
    if date is None:
        expense_date = datetime.now()
    else:
        expense_date = datetime.fromisoformat(date)
    
    expense = Expense(
        amount=amount,
        category=category,
        description=description,
        date=expense_date
    )
    
    expense_id = save_expense(expense)
    return f"Expense added successfully with ID: {expense_id}"

@tool
def get_expense_summary(category: Optional[str] = None, period: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a summary of expenses, optionally filtered by category and time period.
    
    Args:
        category: Optional category to filter by
        period: Optional time period ('week', 'month', 'year'). Defaults to all time.
    """
    start_date = None
    if period:
        now = datetime.now()
        if period == 'week':
            start_date = datetime(now.year, now.month, now.day - now.weekday())
        elif period == 'month':
            start_date = datetime(now.year, now.month, 1)
        elif period == 'year':
            start_date = datetime(now.year, 1, 1)
    
    expenses = get_expenses(category=category, start_date=start_date)
    
    # Calculate summary statistics
    total = sum(expense.amount for expense in expenses)
    
    # Group by category
    categories = {}
    for expense in expenses:
        if expense.category not in categories:
            categories[expense.category] = 0
        categories[expense.category] += expense.amount
    
    return {
        "total": total,
        "count": len(expenses),
        "by_category": categories,
        "period": period or "all time",
        "category_filter": category or "all categories"
    }

@tool
def suggest_budget() -> Dict[str, Any]:
    """
    Suggest a budget based on past expenses.
    """
    # Get expenses from the last 3 months
    now = datetime.now()
    three_months_ago = datetime(now.year, now.month - 3 if now.month > 3 else now.month + 9, 1)
    expenses = get_expenses(start_date=three_months_ago)
    
    if not expenses:
        return {"error": "No expense data available to suggest a budget"}
    
    # Calculate average monthly expenses by category
    categories = {}
    for expense in expenses:
        if expense.category not in categories:
            categories[expense.category] = 0
        categories[expense.category] += expense.amount
    
    # Get average monthly total
    total_expenses = sum(categories.values())
    months = (now.year - three_months_ago.year) * 12 + now.month - three_months_ago.month
    avg_monthly = total_expenses / max(1, months)
    
    # Normalize category values to suggested monthly amounts
    for category in categories:
        categories[category] = categories[category] / max(1, months)
    
    return {
        "suggested_monthly_budget": avg_monthly,
        "suggested_allocations": categories
    }

@tool
def analyze_spending_trend(category: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze spending trends over time, optionally for a specific category.
    
    Args:
        category: Optional category to analyze
    """
    now = datetime.now()
    one_year_ago = datetime(now.year - 1, now.month, 1)
    
    expenses = get_expenses(category=category, start_date=one_year_ago)
    
    if not expenses:
        return {"error": "No expense data available for trend analysis"}
    
    # Group by month
    monthly_totals = {}
    for expense in expenses:
        month_key = f"{expense.date.year}-{expense.date.month:02d}"
        if month_key not in monthly_totals:
            monthly_totals[month_key] = 0
        monthly_totals[month_key] += expense.amount
    
    # Calculate trend (simple moving average)
    months = sorted(monthly_totals.keys())
    values = [monthly_totals[month] for month in months]
    
    trend = "increasing" if len(values) > 1 and values[-1] > values[0] else "decreasing"
    
    return {
        "monthly_totals": monthly_totals,
        "trend": trend,
        "average_monthly": sum(values) / len(values),
        "category": category or "all categories"
    }

# List of tools that can be exported
tools = [add_expense, get_expense_summary, suggest_budget, analyze_spending_trend]