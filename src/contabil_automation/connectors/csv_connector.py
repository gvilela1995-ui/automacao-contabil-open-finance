from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from src.contabil_automation.models import BankTransaction


def load_transactions(path: Path) -> list[BankTransaction]:
    transactions: list[BankTransaction] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            transactions.append(
                BankTransaction(
                    client_id=(row.get("client_id") or "").strip(),
                    account_id=(row.get("account_id") or "").strip(),
                    date=datetime.strptime((row.get("date") or "").strip(), "%Y-%m-%d").date(),
                    description=(row.get("description") or "").strip(),
                    amount=float((row.get("amount") or "0").replace(",", ".")),
                    type=(row.get("type") or "").strip().lower(),
                    transaction_id=(row.get("transaction_id") or "").strip(),
                )
            )
    return transactions
