from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.contabil_automation.models import BankTransaction, ClassifiedTransaction


@dataclass(frozen=True)
class CategoryRule:
    priority: int
    keyword: str
    category: str
    debit_account: str
    credit_account: str
    history_code: str
    history: str
    requires_receipt: bool = False


def load_rules(path: Path) -> list[CategoryRule]:
    rules: list[CategoryRule] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            rules.append(
                CategoryRule(
                    priority=int(row.get("prioridade") or 999),
                    keyword=(row.get("palavra_chave") or "").strip().upper(),
                    category=(row.get("categoria") or "A Classificar").strip(),
                    debit_account=(row.get("conta_debito") or "").strip(),
                    credit_account=(row.get("conta_credito") or "").strip(),
                    history_code=(row.get("codigo_historico") or "").strip(),
                    history=(row.get("historico_padrao") or "").strip(),
                    requires_receipt=(row.get("exige_comprovante") or "").strip().lower() in {"sim", "s", "true", "1"},
                )
            )
    return sorted(rules, key=lambda rule: rule.priority)


def classify(transaction: BankTransaction, rules: list[CategoryRule]) -> ClassifiedTransaction:
    description = transaction.description.upper()
    fallback = rules[-1]

    for rule in rules:
        if rule.keyword and rule.keyword in description:
            return ClassifiedTransaction(transaction, rule.category, rule.debit_account, rule.credit_account, rule.history_code, rule.history, rule.requires_receipt)

    return ClassifiedTransaction(transaction, fallback.category, fallback.debit_account, fallback.credit_account, fallback.history_code, fallback.history, fallback.requires_receipt)


def classify_all(transactions: list[BankTransaction], rules: list[CategoryRule]) -> list[ClassifiedTransaction]:
    return [classify(transaction, rules) for transaction in transactions]
