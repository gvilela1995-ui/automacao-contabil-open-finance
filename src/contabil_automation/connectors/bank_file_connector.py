from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

from src.contabil_automation.models import BankTransaction


def parse_money(value: str) -> float:
    value = (value or "0").strip().replace("R$", "").replace(" ", "")
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    return float(value or "0")


def parse_date(value: str):
    value = (value or "").strip()
    value = re.sub(r"\[.*?\]", "", value)
    value = value[:8] if re.match(r"^\d{8}", value) else value
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Data invalida: {value}")


def tag_value(block: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)(?:\r?\n|<)", block, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def stable_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def load_ofx(path: Path, client_id: str, account_id: str) -> list[BankTransaction]:
    text = path.read_text(encoding="latin-1", errors="ignore")
    blocks = re.findall(r"<STMTTRN>(.*?)(?=<STMTTRN>|</BANKTRANLIST>|</STMTTRN>)", text, flags=re.IGNORECASE | re.DOTALL)
    transactions: list[BankTransaction] = []
    for block in blocks:
        amount = parse_money(tag_value(block, "TRNAMT"))
        description = tag_value(block, "MEMO") or tag_value(block, "NAME") or tag_value(block, "TRNTYPE")
        posted_at = parse_date(tag_value(block, "DTPOSTED"))
        transaction_id = tag_value(block, "FITID") or stable_id(client_id, account_id, posted_at.isoformat(), description, str(amount))
        transactions.append(
            BankTransaction(
                client_id=client_id,
                account_id=account_id,
                date=posted_at,
                description=" ".join(description.split()),
                amount=abs(amount),
                type="credit" if amount >= 0 else "debit",
                transaction_id=transaction_id,
            )
        )
    return transactions


def first_value(row: dict[str, str], names: list[str]) -> str:
    normalized = {normalize_key(key): value for key, value in row.items()}
    for name in names:
        value = normalized.get(normalize_key(name), "")
        if value:
            return value
    return ""


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def detect_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8-sig", errors="ignore")[:2048]
    return ";" if sample.count(";") >= sample.count(",") else ","


def load_bank_csv(path: Path, client_id: str, account_id: str) -> list[BankTransaction]:
    delimiter = detect_delimiter(path)
    transactions: list[BankTransaction] = []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        for row in reader:
            date_value = first_value(row, ["date", "data", "dt", "lançamento", "lancamento"])
            description = first_value(row, ["description", "descricao", "descrição", "historico", "histórico", "memo"])
            amount_raw = first_value(row, ["amount", "valor", "vlr"])
            debit = first_value(row, ["debito", "débito", "saída", "saida"])
            credit = first_value(row, ["credito", "crédito", "entrada"])
            if not amount_raw and (debit or credit):
                amount = parse_money(credit or debit)
                transaction_type = "credit" if credit else "debit"
            else:
                amount = parse_money(amount_raw)
                transaction_type = "credit" if amount >= 0 else "debit"
            date = parse_date(date_value)
            transaction_id = first_value(row, ["transaction_id", "id", "documento", "fitid"]) or stable_id(client_id, account_id, date.isoformat(), description, str(amount))
            transactions.append(
                BankTransaction(
                    client_id=client_id,
                    account_id=account_id,
                    date=date,
                    description=" ".join(description.split()),
                    amount=abs(amount),
                    type=transaction_type,
                    transaction_id=transaction_id,
                )
            )
    return transactions


def load_bank_file(path: Path, client_id: str, account_id: str) -> list[BankTransaction]:
    suffix = path.suffix.lower()
    if suffix == ".ofx":
        return load_ofx(path, client_id, account_id)
    if suffix in {".csv", ".txt"}:
        return load_bank_csv(path, client_id, account_id)
    raise ValueError("Formato nao suportado. Use OFX ou CSV.")


def write_normalized_csv(path: Path, transactions: list[BankTransaction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["client_id", "account_id", "date", "description", "amount", "type", "transaction_id"],
            delimiter=";",
        )
        writer.writeheader()
        for transaction in transactions:
            writer.writerow(
                {
                    "client_id": transaction.client_id,
                    "account_id": transaction.account_id,
                    "date": transaction.date.isoformat(),
                    "description": transaction.description,
                    "amount": f"{transaction.amount:.2f}",
                    "type": transaction.type,
                    "transaction_id": transaction.transaction_id,
                }
            )
