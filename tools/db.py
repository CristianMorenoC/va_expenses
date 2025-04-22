import json
import os
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional

from tools.schemas import Expense, Income, Budget, UserProfile
from config import DB_PATH

# Get the database directory path
DB_DIR = os.path.dirname(DB_PATH)

# Constants for file paths
EXPENSES_FILE = os.path.join(DB_DIR, "expenses.json")
INCOMES_FILE = os.path.join(DB_DIR, "incomes.json")
BUDGETS_FILE = os.path.join(DB_DIR, "budgets.json")
PROFILES_FILE = os.path.join(DB_DIR, "profiles.json")

# Ensure the database directory exists
os.makedirs(DB_DIR, exist_ok=True)

# Helper functions for JSON operations
def _read_json_file(file_path: str) -> List[Dict]:
    """Read data from a JSON file, creating it if it doesn't exist."""
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)
        return []
    
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _write_json_file(file_path: str, data: List[Dict]) -> None:
    """Write data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def init_db():
    """Initialize the database with required files."""
    print(f"Initializing JSON database in {DB_DIR}")
    # Create empty JSON files if they don't exist
    _read_json_file(EXPENSES_FILE)
    _read_json_file(INCOMES_FILE)
    _read_json_file(BUDGETS_FILE)
    _read_json_file(PROFILES_FILE)
    print(f"Database files created: {os.path.basename(EXPENSES_FILE)}, {os.path.basename(INCOMES_FILE)}, {os.path.basename(BUDGETS_FILE)}, {os.path.basename(PROFILES_FILE)}")

def save_expense(expense: Expense) -> str:
    """Save an expense to the JSON store."""
    expenses = _read_json_file(EXPENSES_FILE)
    
    if not expense.id:
        expense.id = str(uuid.uuid4())
    
    # Convert expense to dictionary
    expense_dict = {
        "id": expense.id,
        "amount": expense.amount,
        "category": expense.category,
        "description": expense.description,
        "date": expense.date.isoformat()
    }
    
    # Update existing or add new
    found = False
    for i, existing in enumerate(expenses):
        if existing["id"] == expense.id:
            expenses[i] = expense_dict
            found = True
            break
    
    if not found:
        expenses.append(expense_dict)
    
    _write_json_file(EXPENSES_FILE, expenses)
    return expense.id

def get_expenses(category: Optional[str] = None, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> List[Expense]:
    """Retrieve expenses from the JSON store with optional filtering."""
    expenses = _read_json_file(EXPENSES_FILE)
    result = []
    
    # Apply filters
    for expense_dict in expenses:
        # Check category filter
        if category and expense_dict["category"] != category:
            continue
        
        # Parse date for comparison
        expense_date = datetime.fromisoformat(expense_dict["date"])
        
        # Check date filters
        if start_date and expense_date < start_date:
            continue
        if end_date and expense_date > end_date:
            continue
        
        # Add matching expense to results
        result.append(Expense(
            id=expense_dict["id"],
            amount=expense_dict["amount"],
            category=expense_dict["category"],
            description=expense_dict["description"],
            date=expense_date
        ))
    
    return result

def save_income(income: Income) -> str:
    """Save an income entry to the JSON store."""
    incomes = _read_json_file(INCOMES_FILE)
    
    if not income.id:
        income.id = str(uuid.uuid4())
    
    # Convert income to dictionary
    income_dict = {
        "id": income.id,
        "amount": income.amount,
        "source": income.source,
        "description": income.description,
        "date": income.date.isoformat()
    }
    
    # Update existing or add new
    found = False
    for i, existing in enumerate(incomes):
        if existing["id"] == income.id:
            incomes[i] = income_dict
            found = True
            break
    
    if not found:
        incomes.append(income_dict)
    
    _write_json_file(INCOMES_FILE, incomes)
    return income.id

def save_budget(budget: Budget) -> str:
    """Save a budget to the JSON store."""
    budgets = _read_json_file(BUDGETS_FILE)
    
    budget_id = str(uuid.uuid4())
    
    # Convert budget to dictionary
    budget_dict = {
        "id": budget_id,
        "total": budget.total,
        "allocations": budget.allocations,
        "period": budget.period,
        "start_date": budget.start_date.isoformat(),
        "end_date": budget.end_date.isoformat() if budget.end_date else None
    }
    
    budgets.append(budget_dict)
    _write_json_file(BUDGETS_FILE, budgets)
    return budget_id

def get_latest_budget() -> Optional[Budget]:
    """Get the most recent budget from the JSON store."""
    budgets = _read_json_file(BUDGETS_FILE)
    
    if not budgets:
        return None
    
    # Sort by start_date and get the latest
    budgets.sort(key=lambda x: x["start_date"], reverse=True)
    latest = budgets[0]
    
    return Budget(
        total=latest["total"],
        allocations=latest["allocations"],
        period=latest["period"],
        start_date=datetime.fromisoformat(latest["start_date"]),
        end_date=datetime.fromisoformat(latest["end_date"]) if latest["end_date"] else None
    )

# Initialize the JSON files when the module is imported
init_db() 