from __future__ import annotations

import json
from pathlib import Path

from src.contabil_automation.models import ClassifiedTransaction


def format_amount(value: float, decimal_separator: str) -> str:
    formatted = f"{abs(value):.2f}"
    if decimal_separator != ".":
        formatted = formatted.replace(".", decimal_separator)
    return formatted


def build_line(item: ClassifiedTransaction, layout: dict) -> str:
    transaction = item.transaction
    values = {
        "data": transaction.date.strftime(layout.get("date_format", "%d/%m/%Y")),
        "debito": item.debit_account,
        "credito": item.credit_account,
        "valor": format_amount(transaction.amount, layout.get("decimal_separator", ",")),
        "codigo_historico": item.history_code,
        "historico": item.history or transaction.description,
    }
    delimiter = layout.get("delimiter", ";")
    return delimiter.join(values[field] for field in layout["fields"])


def export_txt(items: list[ClassifiedTransaction], layout_path: Path, output_path: Path) -> None:
    layout = json.loads(layout_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [build_line(item, layout) for item in items]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
