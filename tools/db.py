import sqlite3
from datetime import datetime
import json
import uuid
import os
from typing import List, Dict, Any, Optional

from tools.schemas import Expense, Income, Budget, UserProfile
from config import DB_PATH

# Ensure the database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create expenses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id TEXT PRIMARY KEY,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL
    )
    ''')
    
    # Create incomes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS incomes (
        id TEXT PRIMARY KEY,
        amount REAL NOT NULL,
        source TEXT NOT NULL,
        description TEXT,
        date TEXT NOT NULL
    )
    ''')
    
    # Create budgets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        id TEXT PRIMARY KEY,
        total REAL NOT NULL,
        allocations TEXT NOT NULL,
        period TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT
    )
    ''')
    
    # Create user profile table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_profiles (
        name TEXT PRIMARY KEY,
        income REAL NOT NULL,
        savings_goal REAL,
        risk_tolerance TEXT,
        preferences TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def save_expense(expense: Expense) -> str:
    """Save an expense to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if not expense.id:
        expense.id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT OR REPLACE INTO expenses (id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
        (
            expense.id,
            expense.amount,
            expense.category,
            expense.description,
            expense.date.isoformat()
        )
    )
    
    conn.commit()
    conn.close()
    return expense.id

def get_expenses(category: Optional[str] = None, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> List[Expense]:
    """Retrieve expenses from the database with optional filtering."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT id, amount, category, description, date FROM expenses"
    params = []
    
    # Build the query based on filters
    conditions = []
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date.isoformat())
    
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date.isoformat())
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    expenses = []
    for row in rows:
        expenses.append(Expense(
            id=row[0],
            amount=row[1],
            category=row[2],
            description=row[3],
            date=datetime.fromisoformat(row[4])
        ))
    
    conn.close()
    return expenses

# Similar functions for income, budgets, and user profiles
def save_income(income: Income) -> str:
    """Save an income entry to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if not income.id:
        income.id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT OR REPLACE INTO incomes (id, amount, source, description, date) VALUES (?, ?, ?, ?, ?)",
        (
            income.id,
            income.amount,
            income.source,
            income.description,
            income.date.isoformat()
        )
    )
    
    conn.commit()
    conn.close()
    return income.id

def save_budget(budget: Budget) -> str:
    """Save a budget to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    budget_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO budgets (id, total, allocations, period, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?)",
        (
            budget_id,
            budget.total,
            json.dumps(budget.allocations),
            budget.period,
            budget.start_date.isoformat(),
            budget.end_date.isoformat() if budget.end_date else None
        )
    )
    
    conn.commit()
    conn.close()
    return budget_id

def get_latest_budget() -> Optional[Budget]:
    """Get the most recent budget."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, total, allocations, period, start_date, end_date FROM budgets ORDER BY start_date DESC LIMIT 1"
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return Budget(
        total=row[1],
        allocations=json.loads(row[2]),
        period=row[3],
        start_date=datetime.fromisoformat(row[4]),
        end_date=datetime.fromisoformat(row[5]) if row[5] else None
    )

# Initialize the database when the module is imported
init_db() 