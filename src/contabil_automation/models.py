from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BankTransaction:
    client_id: str
    account_id: str
    date: date
    description: str
    amount: float
    type: str
    transaction_id: str


@dataclass(frozen=True)
class ClassifiedTransaction:
    transaction: BankTransaction
    category: str
    debit_account: str
    credit_account: str
    history_code: str
    history: str
    requires_receipt: bool = False
