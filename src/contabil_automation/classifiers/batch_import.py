from __future__ import annotations

import argparse
import csv
from pathlib import Path


FIELDNAMES = [
    "prioridade",
    "palavra_chave",
    "categoria",
    "conta_debito",
    "conta_credito",
    "codigo_historico",
    "historico_padrao",
    "exige_comprovante",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(file, delimiter=";")]


def normalize_keyword(value: str) -> str:
    return (value or "").strip().upper()


def import_batch(batch_path: Path, rules_path: Path) -> int:
    existing = read_rows(rules_path) if rules_path.exists() else []
    by_keyword = {normalize_keyword(row.get("palavra_chave", "")): row for row in existing if normalize_keyword(row.get("palavra_chave", ""))}

    batch = read_rows(batch_path)
    next_priority = 10
    if existing:
        priorities = [int(row.get("prioridade") or 999) for row in existing if (row.get("prioridade") or "").isdigit()]
        next_priority = max(priorities or [0]) + 10

    imported = 0
    for row in batch:
        keyword = normalize_keyword(row.get("palavra_chave", ""))
        if not keyword:
            continue
        record = {
            "prioridade": str(next_priority),
            "palavra_chave": keyword,
            "categoria": (row.get("categoria") or "A Classificar").strip(),
            "conta_debito": (row.get("conta_debito") or "").strip(),
            "conta_credito": (row.get("conta_credito") or "").strip(),
            "codigo_historico": (row.get("codigo_historico") or "").strip(),
            "historico_padrao": (row.get("historico_padrao") or "").strip(),
            "exige_comprovante": (row.get("exige_comprovante") or "nao").strip(),
        }
        if keyword in by_keyword:
            record["prioridade"] = by_keyword[keyword].get("prioridade", record["prioridade"])
        else:
            next_priority += 10
        by_keyword[keyword] = record
        imported += 1

    fallback = next((row for row in existing if not normalize_keyword(row.get("palavra_chave", ""))), None)
    output_rows = sorted(by_keyword.values(), key=lambda row: int(row.get("prioridade") or 999))
    if fallback:
        output_rows.append(fallback)
    else:
        output_rows.append(
            {
                "prioridade": "999",
                "palavra_chave": "",
                "categoria": "A Classificar",
                "conta_debito": "9.9.9.99",
                "conta_credito": "9.9.9.99",
                "codigo_historico": "9999",
                "historico_padrao": "Lancamento bancario a classificar",
                "exige_comprovante": "nao",
            }
        )

    with rules_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES, delimiter=";")
        writer.writeheader()
        writer.writerows(output_rows)

    return imported


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa classificacoes em lote para as regras contabeis.")
    parser.add_argument("--batch", default="data/input/classificacao_lote.csv", help="CSV com classificacoes em lote.")
    parser.add_argument("--rules", default="config/categorias.csv", help="CSV de regras do sistema.")
    args = parser.parse_args()

    imported = import_batch(Path(args.batch), Path(args.rules))
    print(f"Classificacoes importadas/atualizadas: {imported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
