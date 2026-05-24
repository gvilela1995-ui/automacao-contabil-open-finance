from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.contabil_automation.classifiers.batch_import import import_batch


def build_batch_from_repeated(repeated_csv: Path, batch_csv: Path) -> int:
    batch_csv.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with repeated_csv.open("r", encoding="utf-8-sig", newline="") as source, batch_csv.open("w", encoding="utf-8-sig", newline="") as target:
        reader = csv.DictReader(source, delimiter=";")
        writer = csv.DictWriter(
            target,
            fieldnames=["palavra_chave", "categoria", "conta_debito", "conta_credito", "codigo_historico", "historico_padrao"],
            delimiter=";",
        )
        writer.writeheader()
        for row in reader:
            if (row.get("aplicar_mesma_classificacao") or "").strip().lower() not in {"sim", "s", "true", "1"}:
                continue
            writer.writerow(
                {
                    "palavra_chave": row.get("descricao_repetida", ""),
                    "categoria": row.get("categoria_atual", "") or "A Classificar",
                    "conta_debito": row.get("conta_debito", ""),
                    "conta_credito": row.get("conta_credito", ""),
                    "codigo_historico": row.get("codigo_historico", ""),
                    "historico_padrao": row.get("historico_padrao", ""),
                }
            )
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica classificacoes aprovadas para descricoes repetidas.")
    parser.add_argument("--repeated", default="data/output/classificacao_repetidos.csv")
    parser.add_argument("--rules", default="config/categorias.csv")
    parser.add_argument("--batch", default="data/output/classificacao_repetidos_aprovadas.csv")
    args = parser.parse_args()

    count = build_batch_from_repeated(Path(args.repeated), Path(args.batch))
    imported = import_batch(Path(args.batch), Path(args.rules))
    print(f"Repetidos aprovados: {count}")
    print(f"Regras atualizadas: {imported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
