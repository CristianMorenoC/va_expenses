from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config import LLM_MODEL

from tools.utils import suggest_budget, analyze_spending_trend, get_expense_summary

ADVISOR_SYSTEM_PROMPT = """You are an expert financial advisor specializing in personal budgeting and expense management.
Your job is to help users understand their spending patterns and provide actionable advice to help them meet their financial goals.

When advising users:
- Be specific and personalized, referencing their actual spending data
- Provide clear, actionable recommendations
- Explain the reasoning behind your advice
- Be encouraging and positive, even when suggesting changes
- Use data and numbers to support your recommendations

You have access to the user's expense data and can analyze their spending patterns across categories.
Your goal is to help them create a sustainable budget and develop better financial habits.
"""

class FinancialAdvisor:
    """Provides personalized financial advice based on user's spending data."""
    
    def __init__(self):
        self.llm = ChatAnthropic(model=LLM_MODEL, temperature=0.2)  # Slightly more creative
        
    def generate_advice(self, query: str, financial_data: Dict[str, Any]) -> str:
        """
        Generate personalized financial advice based on the user's query and data.
        
        Args:
            query: The user's question or request
            financial_data: Dictionary with the user's financial data
            
        Returns:
            A string with personalized financial advice
        """
        # Format the financial data as a readable string
        data_str = self._format_financial_data(financial_data)
        
        messages = [
            SystemMessage(content=ADVISOR_SYSTEM_PROMPT),
            SystemMessage(content=f"User's financial data:\n{data_str}"),
            HumanMessage(content=query)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def create_budget_plan(self, income: float, categories: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Create a recommended budget plan based on income and optional category spending.
        
        Args:
            income: User's monthly income
            categories: Optional dictionary of spending by category
            
        Returns:
            A dictionary with budget recommendations
        """
        # If no categories provided, get recommended allocations
        if not categories:
            budget_suggestion = suggest_budget()
            if "error" in budget_suggestion:
                # Use general guidelines if no data available
                categories = {
                    "housing": 0.30,
                    "food": 0.15,
                    "transportation": 0.10,
                    "utilities": 0.10,
                    "health": 0.05,
                    "entertainment": 0.05,
                    "saving": 0.20,
                    "other": 0.05
                }
                allocations = {cat: income * pct for cat, pct in categories.items()}
            else:
                # Scale the suggested allocations to the income
                suggested = budget_suggestion["suggested_allocations"]
                total_suggested = sum(suggested.values())
                scale_factor = income / total_suggested if total_suggested > 0 else 1
                allocations = {cat: amt * scale_factor for cat, amt in suggested.items()}
                
                # Ensure savings category exists
                if "saving" not in allocations:
                    allocations["saving"] = income * 0.20
                    # Adjust other categories proportionally
                    total_without_savings = sum(v for k, v in allocations.items() if k != "saving")
                    if total_without_savings > income * 0.80:
                        adjust_factor = (income * 0.80) / total_without_savings
                        for k in allocations:
                            if k != "saving":
                                allocations[k] *= adjust_factor
        else:
            # Use provided categories and ensure they don't exceed income
            total_expenses = sum(categories.values())
            savings_amount = max(0, income - total_expenses)
            allocations = categories.copy()
            allocations["saving"] = savings_amount
            
        # Create budget recommendation message
        budget_message = self._generate_budget_recommendation(income, allocations)
        
        return {
            "monthly_income": income,
            "allocations": allocations,
            "total_allocated": sum(allocations.values()),
            "recommendation": budget_message
        }
    
    def _format_financial_data(self, financial_data: Dict[str, Any]) -> str:
        """Format financial data as a readable string for the LLM."""
        sections = []
        
        if "expense_summary" in financial_data:
            summary = financial_data["expense_summary"]
            sections.append(f"EXPENSE SUMMARY ({summary.get('period', 'all time')}):")
            sections.append(f"Total: ${summary.get('total', 0):.2f}")
            sections.append(f"Number of expenses: {summary.get('count', 0)}")
            
            if "by_category" in summary:
                sections.append("Breakdown by category:")
                for cat, amt in summary["by_category"].items():
                    sections.append(f"  - {cat}: ${amt:.2f}")
        
        if "budget" in financial_data:
            budget = financial_data["budget"]
            sections.append("\nCURRENT BUDGET:")
            sections.append(f"Total budget: ${budget.get('total', 0):.2f}")
            
            if "allocations" in budget:
                sections.append("Allocations:")
                for cat, amt in budget["allocations"].items():
                    sections.append(f"  - {cat}: ${amt:.2f}")
        
        if "trends" in financial_data:
            trends = financial_data["trends"]
            sections.append("\nSPENDING TRENDS:")
            sections.append(f"Overall trend: {trends.get('trend', 'unknown')}")
            sections.append(f"Average monthly: ${trends.get('average_monthly', 0):.2f}")
            
            if "monthly_totals" in trends:
                sections.append("Monthly spending:")
                for month, total in sorted(trends["monthly_totals"].items()):
                    sections.append(f"  - {month}: ${total:.2f}")
        
        return "\n".join(sections)
    
    def _generate_budget_recommendation(self, income: float, allocations: Dict[str, float]) -> str:
        """Generate a textual budget recommendation."""
        prompt = f"""
        Based on a monthly income of ${income:.2f}, here is a recommended budget breakdown:
        
        {', '.join(f'{cat}: ${amt:.2f} ({(amt/income*100):.1f}%)' for cat, amt in allocations.items())}
        
        Please provide a personalized explanation for this budget allocation and any recommendations for adjustments based on common financial best practices.
        """
        
        messages = [
            SystemMessage(content=ADVISOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content

# Usage example:
# advisor = FinancialAdvisor()
# advice = advisor.generate_advice("How can I reduce my food expenses?", 
#                                  {"expense_summary": get_expense_summary()})
# print(advice) 