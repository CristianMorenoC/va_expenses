from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import calendar

from tools.db import get_expenses, get_latest_budget

class ExpenseRetriever:
    """Retrieves and formats expense data for the agent."""
    
    def get_expense_data(self, 
                        category: Optional[str] = None, 
                        period: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Retrieve expense data with optional filtering.
        
        Args:
            category: Optional category to filter expenses
            period: Optional time period ('week', 'month', 'year', 'custom')
            start_date: Optional custom start date (only used if period='custom')
            end_date: Optional custom end date (only used if period='custom')
            
        Returns:
            Dictionary with formatted expense data
        """
        # Determine date range
        if period and period != 'custom':
            start_date, end_date = self._get_date_range(period)
        
        # Get expenses from the database
        expenses = get_expenses(category=category, start_date=start_date, end_date=end_date)
        
        # Calculate summary statistics
        total_spent = sum(expense.amount for expense in expenses)
        
        # Group by category
        by_category = {}
        for expense in expenses:
            if expense.category not in by_category:
                by_category[expense.category] = 0
            by_category[expense.category] += expense.amount
            
        # Group by date
        by_date = {}
        for expense in expenses:
            date_str = expense.date.strftime('%Y-%m-%d')
            if date_str not in by_date:
                by_date[date_str] = 0
            by_date[date_str] += expense.amount
        
        return {
            "expenses": [self._format_expense(e) for e in expenses],
            "total": total_spent,
            "count": len(expenses),
            "by_category": by_category,
            "by_date": by_date,
            "period": period or "all time",
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    
    def get_budget_comparison(self, period: str = 'month') -> Dict[str, Any]:
        """
        Compare actual spending to budget.
        
        Args:
            period: Time period for comparison ('week', 'month', 'year')
            
        Returns:
            Dictionary with budget comparison data
        """
        # Get current budget
        budget = get_latest_budget()
        if not budget:
            return {"error": "No budget data available"}
        
        # Get current period's expenses
        start_date, end_date = self._get_date_range(period)
        expenses = get_expenses(start_date=start_date, end_date=end_date)
        
        # Calculate totals by category
        actual_spending = {}
        for expense in expenses:
            if expense.category not in actual_spending:
                actual_spending[expense.category] = 0
            actual_spending[expense.category] += expense.amount
        
        # Compare with budget
        comparison = {}
        for category, budgeted in budget.allocations.items():
            spent = actual_spending.get(category, 0)
            comparison[category] = {
                "budgeted": budgeted,
                "actual": spent,
                "difference": budgeted - spent,
                "percent_used": (spent / budgeted * 100) if budgeted > 0 else 0
            }
        
        # Add categories that exist in spending but not in budget
        for category, spent in actual_spending.items():
            if category not in comparison:
                comparison[category] = {
                    "budgeted": 0,
                    "actual": spent,
                    "difference": -spent,
                    "percent_used": 100  # Since there's no budget, it's 100% over
                }
        
        return {
            "budget_period": budget.period,
            "budget_total": budget.total,
            "actual_total": sum(actual_spending.values()),
            "comparison": comparison,
            "period_covered": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    def _get_date_range(self, period: str) -> tuple[datetime, datetime]:
        """Convert a period string to start and end dates."""
        now = datetime.now()
        
        if period == 'week':
            # Start of current week (Monday)
            start_date = now - timedelta(days=now.weekday())
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            # End of current week (Sunday)
            end_date = start_date + timedelta(days=6)
            end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
        
        elif period == 'month':
            # Start of current month
            start_date = datetime(now.year, now.month, 1)
            # End of current month
            last_day = calendar.monthrange(now.year, now.month)[1]
            end_date = datetime(now.year, now.month, last_day, 23, 59, 59)
        
        elif period == 'year':
            # Start of current year
            start_date = datetime(now.year, 1, 1)
            # End of current year
            end_date = datetime(now.year, 12, 31, 23, 59, 59)
        
        else:
            # Default to last 30 days
            start_date = now - timedelta(days=30)
            end_date = now
        
        return start_date, end_date
    
    def _format_expense(self, expense) -> Dict[str, Any]:
        """Format an expense object as a dictionary."""
        return {
            "id": expense.id,
            "amount": expense.amount,
            "category": expense.category,
            "description": expense.description,
            "date": expense.date.isoformat()
        }

# Usage example:
# retriever = ExpenseRetriever()
# monthly_data = retriever.get_expense_data(period='month')
# print(f"Total monthly expenses: ${monthly_data['total']:.2f}") 