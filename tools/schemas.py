from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Expense:
    """Represents a single expense entry."""
    amount: float
    category: str
    description: str
    date: datetime
    id: Optional[str] = None
    
@dataclass
class Income:
    """Represents an income entry."""
    amount: float
    source: str
    description: str
    date: datetime
    id: Optional[str] = None
    
@dataclass
class Budget:
    """Represents a budget with category allocations."""
    total: float
    allocations: Dict[str, float]  # Category -> Amount
    period: str  # 'monthly', 'weekly', etc.
    start_date: datetime
    end_date: Optional[datetime] = None
    
@dataclass
class UserProfile:
    """User profile with financial goals and preferences."""
    name: str
    income: float
    savings_goal: Optional[float] = None
    risk_tolerance: Optional[str] = None  # 'low', 'medium', 'high'
    preferences: Optional[Dict[str, Any]] = None 