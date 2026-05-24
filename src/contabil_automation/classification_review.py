from __future__ import annotations

import argparse
import csv
import html
import re
from collections import defaultdict
from pathlib import Path

from src.contabil_automation.classifiers.rules import classify_all, load_rules
from src.contabil_automation.connectors.csv_connector import load_transactions


def normalize_description(value: str) -> str:
    value = re.sub(r"\d{2}/\d{2}/\d{2,4}", "", value or "")
    value = re.sub(r"\d{3,}", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip().upper()


def write_repeated_csv(path: Path, input_csv: Path, rules_csv: Path) -> None:
    transactions = load_transactions(input_csv)
    classified = classify_all(transactions, load_rules(rules_csv))
    groups: dict[str, list] = defaultdict(list)
    for item in classified:
        groups[normalize_description(item.transaction.description)].append(item)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "descricao_repetida",
                "quantidade",
                "total",
                "categoria_atual",
                "conta_debito",
                "conta_credito",
                "codigo_historico",
                "historico_padrao",
                "aplicar_mesma_classificacao",
            ],
            delimiter=";",
        )
        writer.writeheader()
        for description, items in sorted(groups.items(), key=lambda entry: len(entry[1]), reverse=True):
            if len(items) < 2:
                continue
            first = items[0]
            writer.writerow(
                {
                    "descricao_repetida": description,
                    "quantidade": len(items),
                    "total": f"{sum(item.transaction.amount for item in items):.2f}",
                    "categoria_atual": first.category,
                    "conta_debito": first.debit_account,
                    "conta_credito": first.credit_account,
                    "codigo_historico": first.history_code,
                    "historico_padrao": first.history,
                    "aplicar_mesma_classificacao": "sim",
                }
            )


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(file, delimiter=";")]


def write_review_html(path: Path, repeated_csv: Path) -> None:
    rows = read_csv(repeated_csv)
    body_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row.get('descricao_repetida', ''))}</td>"
        f"<td>{html.escape(row.get('quantidade', ''))}</td>"
        f"<td>{html.escape(row.get('total', ''))}</td>"
        f"<td>{html.escape(row.get('categoria_atual', ''))}</td>"
        f"<td>{html.escape(row.get('conta_debito', ''))}</td>"
        f"<td>{html.escape(row.get('conta_credito', ''))}</td>"
        f"<td>{html.escape(row.get('codigo_historico', ''))}</td>"
        f"<td>{html.escape(row.get('historico_padrao', ''))}</td>"
        f"<td>{html.escape(row.get('aplicar_mesma_classificacao', ''))}</td>"
        "</tr>"
        for row in rows
    )
    if not body_rows:
        body_rows = "<tr><td colspan='9'>Nenhuma descrição repetida encontrada.</td></tr>"

    document = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Classificação em Lote</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #172033; }}
    header {{ background: #fff; border-bottom: 1px solid #d8dde6; padding: 22px 28px; }}
    main {{ padding: 24px 28px; }}
    .hint {{ background: #fff7e6; border: 1px solid #ffd591; padding: 12px; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; margin-top: 16px; }}
    th, td {{ border-bottom: 1px solid #e7ebf0; padding: 10px; font-size: 13px; text-align: left; vertical-align: top; }}
    th {{ background: #f9fafb; color: #475467; }}
    code {{ background: #eef2f7; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>Classificação em Lote</h1>
    <p>Descrições repetidas do extrato para acelerar código contábil, histórico e contas.</p>
  </header>
  <main>
    <section class="hint">
      Edite o arquivo <code>{html.escape(str(repeated_csv))}</code>. Para aplicar a mesma classificação a nomes repetidos, deixe <code>aplicar_mesma_classificacao=sim</code>, ajuste débito, crédito, código e histórico, depois rode <code>APLICAR_CLASSIFICACAO_REPETIDOS.bat</code>.
    </section>
    <table>
      <thead>
        <tr><th>Descrição repetida</th><th>Qtd</th><th>Total</th><th>Categoria</th><th>Débito</th><th>Crédito</th><th>Cód. Hist.</th><th>Histórico</th><th>Aplicar?</th></tr>
      </thead>
      <tbody>{body_rows}</tbody>
    </table>
  </main>
</body>
</html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera tela/CSV de classificacao por descricoes repetidas.")
    parser.add_argument("--input", default="data/input/transacoes_upload.csv")
    parser.add_argument("--rules", default="config/categorias.csv")
    parser.add_argument("--output-csv", default="data/output/classificacao_repetidos.csv")
    parser.add_argument("--output-html", default="data/output/classificacao_repetidos.html")
    args = parser.parse_args()

    write_repeated_csv(Path(args.output_csv), Path(args.input), Path(args.rules))
    write_review_html(Path(args.output_html), Path(args.output_csv))
    print(f"Tela de classificacao: {args.output_html}")
    print(f"CSV editavel: {args.output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
