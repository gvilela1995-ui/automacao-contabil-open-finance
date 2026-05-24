from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from src.contabil_automation.classifiers.rules import classify_all, load_rules
from src.contabil_automation.connectors.csv_connector import load_transactions
from src.contabil_automation.domain.dominio_excel import export_xlsx
from src.contabil_automation.domain.dominio_txt import export_txt
from src.contabil_automation.models import ClassifiedTransaction
from src.contabil_automation.operations import (
    build_operational_status,
    load_clients,
    load_simple_csv,
    write_clients_status_csv,
    write_dashboard,
)


def write_classified_csv(path: Path, items: list[ClassifiedTransaction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "client_id",
                "account_id",
                "date",
                "description",
                "amount",
                "type",
                "transaction_id",
                "category",
                "debit_account",
                "credit_account",
                "history_code",
                "history",
            ],
            delimiter=";",
        )
        writer.writeheader()
        for item in items:
            transaction = item.transaction
            writer.writerow(
                {
                    "client_id": transaction.client_id,
                    "account_id": transaction.account_id,
                    "date": transaction.date.isoformat(),
                    "description": transaction.description,
                    "amount": f"{transaction.amount:.2f}",
                    "type": transaction.type,
                    "transaction_id": transaction.transaction_id,
                    "category": item.category,
                    "debit_account": item.debit_account,
                    "credit_account": item.credit_account,
                    "history_code": item.history_code,
                    "history": item.history,
                }
            )


def write_report(path: Path, items: list[ClassifiedTransaction]) -> None:
    totals_by_category: dict[str, float] = {}
    unclassified = 0
    for item in items:
        totals_by_category[item.category] = totals_by_category.get(item.category, 0) + item.transaction.amount
        if item.category == "A Classificar":
            unclassified += 1

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "transactions": len(items),
        "unclassified": unclassified,
        "totals_by_category": totals_by_category,
    }
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def group_by_client(items: list[ClassifiedTransaction]) -> dict[str, list[ClassifiedTransaction]]:
    grouped: dict[str, list[ClassifiedTransaction]] = {}
    for item in items:
        grouped.setdefault(item.transaction.client_id, []).append(item)
    return grouped


def export_ready_documents(
    output_dir: Path,
    layout_path: Path,
    classified: list[ClassifiedTransaction],
    operational_status: dict,
) -> None:
    ready_dir = output_dir / "documentos_prontos"
    pending_dir = output_dir / "pendencias"
    ready_dir.mkdir(parents=True, exist_ok=True)
    pending_dir.mkdir(parents=True, exist_ok=True)

    grouped = group_by_client(classified)
    ready_clients = [
        client["client_id"]
        for client in operational_status["clients"]
        if client["etapa_codigo"] == "pronto_dominio"
    ]

    manifest_lines = ["client_id;arquivo_txt;arquivo_excel;transacoes;status"]
    for client_id in ready_clients:
        client_items = grouped.get(client_id, [])
        if not client_items:
            continue
        output_path = ready_dir / f"{client_id}_dominio.txt"
        excel_path = ready_dir / f"{client_id}_conferencia.xlsx"
        export_txt(client_items, layout_path, output_path)
        export_xlsx(client_items, excel_path)
        manifest_lines.append(f"{client_id};{output_path.name};{excel_path.name};{len(client_items)};pronto")

    (ready_dir / "manifesto.csv").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    pending_clients = [
        client
        for client in operational_status["clients"]
        if client["etapa_codigo"] != "pronto_dominio"
    ]
    with (pending_dir / "clientes_pendentes.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "client_id",
                "nome",
                "status_geral",
                "transacoes",
                "a_classificar",
                "comprovantes_faltantes",
                "conciliacao_pendente",
            ],
            delimiter=";",
        )
        writer.writeheader()
        for client in pending_clients:
            writer.writerow(
                {
                    "client_id": client["client_id"],
                    "nome": client["nome"],
                    "status_geral": client["status_geral"],
                    "transacoes": client["transacoes"],
                    "a_classificar": client["a_classificar"],
                    "comprovantes_faltantes": client["comprovantes_faltantes"],
                    "conciliacao_pendente": client["conciliacao_pendente"],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline contabil Open Finance -> categorias -> TXT Dominio.")
    parser.add_argument("--input", required=True, help="CSV de transacoes normalizadas.")
    parser.add_argument("--clients", default="data/input/clientes.csv", help="Cadastro de clientes.")
    parser.add_argument("--rules", required=True, help="CSV de regras de categorizacao.")
    parser.add_argument("--domain-layout", required=True, help="Layout JSON do TXT Dominio.")
    parser.add_argument("--conciliation", default="data/input/conciliacao_exemplo.csv", help="CSV de status de conciliacao.")
    parser.add_argument("--schedules", default="config/agendamentos.csv", help="CSV de rotinas agendadas.")
    parser.add_argument("--stages", default="config/etapas.csv", help="CSV de etapas operacionais.")
    parser.add_argument("--times", default="data/input/tempos_cliente.csv", help="CSV de tempos por cliente/etapa.")
    parser.add_argument("--errors", default="data/input/erros_coleta.csv", help="CSV de erros de coleta.")
    parser.add_argument("--receipts-dir", default="data/comprovantes", help="Pasta de comprovantes por cliente.")
    parser.add_argument("--output-dir", default="data/output", help="Pasta de saida.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    transactions = load_transactions(Path(args.input))
    rules = load_rules(Path(args.rules))
    classified = classify_all(transactions, rules)
    clients = load_clients(Path(args.clients))
    conciliation = load_simple_csv(Path(args.conciliation))
    schedules = load_simple_csv(Path(args.schedules))
    stages = load_simple_csv(Path(args.stages))
    times = load_simple_csv(Path(args.times))
    errors = load_simple_csv(Path(args.errors))
    operational_status = build_operational_status(clients, classified, conciliation, schedules, stages, times, errors, Path(args.receipts_dir))

    write_classified_csv(output_dir / "lancamentos_classificados.csv", classified)
    export_txt(classified, Path(args.domain_layout), output_dir / "lancamentos_dominio.txt")
    export_xlsx(classified, output_dir / "lancamentos_conferencia.xlsx")
    write_report(output_dir / "relatorio.json", classified)
    (output_dir / "status_operacional.json").write_text(json.dumps(operational_status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_clients_status_csv(output_dir / "clientes_status.csv", operational_status)
    write_dashboard(output_dir / "dashboard.html", operational_status)
    export_ready_documents(output_dir, Path(args.domain_layout), classified, operational_status)

    print(f"Transacoes processadas: {len(classified)}")
    print(f"TXT Dominio: {output_dir / 'lancamentos_dominio.txt'}")
    print(f"Painel gerencial: {output_dir / 'dashboard.html'}")
    print(f"Documentos prontos: {output_dir / 'documentos_prontos'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
