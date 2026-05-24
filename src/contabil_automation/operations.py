from __future__ import annotations

import csv
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.contabil_automation.models import ClassifiedTransaction


@dataclass(frozen=True)
class Client:
    client_id: str
    name: str
    cnpj: str
    owner: str
    active: bool
    open_finance_status: str
    consent_expires_at: str
    frequency: str
    deadline_day: str


def load_clients(path: Path) -> list[Client]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        return [
            Client(
                client_id=(row.get("client_id") or "").strip(),
                name=(row.get("nome") or "").strip(),
                cnpj=(row.get("cnpj") or "").strip(),
                owner=(row.get("responsavel") or "").strip(),
                active=(row.get("ativo") or "").strip().lower() in {"sim", "s", "true", "1"},
                open_finance_status=(row.get("open_finance_status") or "pendente").strip(),
                consent_expires_at=(row.get("consentimento_expira_em") or "").strip(),
                frequency=(row.get("periodicidade") or "").strip(),
                deadline_day=(row.get("dia_limite") or "").strip(),
            )
            for row in reader
            if (row.get("client_id") or "").strip()
        ]


def load_simple_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(file, delimiter=";")]


def parse_datetime(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def minutes_between(start: str, end: str) -> int:
    start_at = parse_datetime(start)
    end_at = parse_datetime(end)
    if not start_at or not end_at:
        return 0
    return max(0, int((end_at - start_at).total_seconds() // 60))


def stage_name(stage_rows: list[dict[str, str]], code: str) -> str:
    for row in stage_rows:
        if (row.get("codigo") or "").strip() == code:
            return (row.get("nome") or code).strip()
    return code


def receipt_exists(receipts_dir: Path, client_id: str, transaction_id: str) -> bool:
    client_dir = receipts_dir / client_id
    if not client_dir.exists():
        return False
    return any(path.is_file() and transaction_id.lower() in path.name.lower() for path in client_dir.rglob("*"))


def build_operational_status(
    clients: list[Client],
    items: list[ClassifiedTransaction],
    conciliation_rows: list[dict[str, str]],
    schedules: list[dict[str, str]],
    stage_rows: list[dict[str, str]],
    time_rows: list[dict[str, str]],
    error_rows: list[dict[str, str]],
    receipts_dir: Path,
) -> dict:
    active_clients = [client for client in clients if client.active]
    items_by_client: dict[str, list[ClassifiedTransaction]] = {}
    for item in items:
        items_by_client.setdefault(item.transaction.client_id, []).append(item)

    conciliation_by_transaction = {
        row.get("transaction_id", ""): (row.get("status", "") or "pendente").strip().lower()
        for row in conciliation_rows
    }
    unresolved_errors = {
        row.get("client_id", "")
        for row in error_rows
        if (row.get("resolvido") or "").strip().lower() not in {"sim", "s", "true", "1"}
    }
    time_by_client: dict[str, int] = {}
    last_time_note: dict[str, str] = {}
    for row in time_rows:
        client_id = row.get("client_id", "")
        duration = minutes_between(row.get("inicio", ""), row.get("fim", ""))
        time_by_client[client_id] = time_by_client.get(client_id, 0) + duration
        if row.get("observacao"):
            last_time_note[client_id] = row.get("observacao", "")

    client_statuses = []
    pending_pull = []
    pending_categorization = []
    pending_receipts = []
    pending_conciliation = []

    for client in active_clients:
        client_items = items_by_client.get(client.client_id, [])
        pulled = len(client_items) > 0
        unclassified = [item for item in client_items if item.category == "A Classificar"]
        missing_receipts = [
            item
            for item in client_items
            if item.requires_receipt and not receipt_exists(receipts_dir, client.client_id, item.transaction.transaction_id)
        ]
        unconciled = [
            item
            for item in client_items
            if conciliation_by_transaction.get(item.transaction.transaction_id, "pendente") != "conciliado"
        ]

        has_error = client.client_id in unresolved_errors
        stage_code = stage_code_for(pulled, unclassified, unconciled, client.open_finance_status, has_error)

        if not pulled:
            pending_pull.append(client.client_id)
        if unclassified:
            pending_categorization.append(client.client_id)
        if missing_receipts:
            pending_receipts.append(client.client_id)
        if unconciled or not pulled:
            pending_conciliation.append(client.client_id)

        client_statuses.append(
            {
                "client_id": client.client_id,
                "nome": client.name,
                "cnpj": client.cnpj,
                "responsavel": client.owner,
                "open_finance_status": client.open_finance_status,
                "consentimento_expira_em": client.consent_expires_at,
                "puxou_extrato": pulled,
                "transacoes": len(client_items),
                "categorizado": pulled and not unclassified,
                "a_classificar": len(unclassified),
                "comprovantes_faltantes": len(missing_receipts),
                "conciliacao_pendente": len(unconciled) if pulled else 1,
                "erros_abertos": 1 if has_error else 0,
                "etapa_codigo": stage_code,
                "etapa_nome": stage_name(stage_rows, stage_code),
                "tempo_total_minutos": time_by_client.get(client.client_id, 0),
                "tempo_medio_por_lancamento": round(time_by_client.get(client.client_id, 0) / len(client_items), 2) if client_items else 0,
                "ultima_observacao_tempo": last_time_note.get(client.client_id, ""),
                "status_geral": status_label(stage_code, stage_rows),
            }
        )

    slowest_client = max(client_statuses, key=lambda row: row["tempo_total_minutos"], default=None)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "clientes_ativos": len(active_clients),
            "clientes_com_extrato_puxado": len([client for client in active_clients if client.client_id not in pending_pull]),
            "clientes_sem_extrato": len(set(pending_pull)),
            "clientes_categorizados": len([status for status in client_statuses if status["categorizado"]]),
            "clientes_com_categoria_pendente": len(set(pending_categorization)),
            "clientes_com_comprovante_pendente": len(set(pending_receipts)),
            "clientes_com_conciliacao_pendente": len(set(pending_conciliation)),
            "clientes_com_erro": len(unresolved_errors),
            "transacoes": len(items),
            "cliente_mais_demorado": slowest_client["nome"] if slowest_client and slowest_client["tempo_total_minutos"] else "",
            "maior_tempo_minutos": slowest_client["tempo_total_minutos"] if slowest_client else 0,
        },
        "clients": client_statuses,
        "schedules": schedules,
        "stages": stage_rows,
    }


def stage_code_for(pulled: bool, unclassified: list, unconciled: list, open_finance_status: str, has_error: bool) -> str:
    if open_finance_status not in {"ativo", "ok"}:
        return "aguardando_consentimento"
    if has_error:
        return "erro_coleta"
    if not pulled:
        return "importar_extrato"
    if unclassified:
        return "classificar"
    if unconciled:
        return "conciliar"
    return "pronto_dominio"


def status_label(stage_code: str, stage_rows: list[dict[str, str]]) -> str:
    return stage_name(stage_rows, stage_code)


def write_clients_status_csv(path: Path, status: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "client_id",
        "nome",
        "cnpj",
        "responsavel",
        "open_finance_status",
        "consentimento_expira_em",
        "puxou_extrato",
        "transacoes",
        "categorizado",
        "a_classificar",
        "comprovantes_faltantes",
        "conciliacao_pendente",
        "erros_abertos",
        "etapa_codigo",
        "etapa_nome",
        "tempo_total_minutos",
        "tempo_medio_por_lancamento",
        "ultima_observacao_tempo",
        "status_geral",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(status["clients"])


def write_dashboard(path: Path, status: dict) -> None:
    metrics = status["metrics"]
    cards = "\n".join(
        f"<section class='metric'><span>{html.escape(label)}</span><strong>{value}</strong></section>"
        for label, value in [
            ("Clientes ativos", metrics["clientes_ativos"]),
            ("Extratos puxados", metrics["clientes_com_extrato_puxado"]),
            ("Faltam puxar", metrics["clientes_sem_extrato"]),
            ("Categorizados", metrics["clientes_categorizados"]),
            ("Categoria pendente", metrics["clientes_com_categoria_pendente"]),
            ("Comprovante pendente", metrics["clientes_com_comprovante_pendente"]),
            ("Conciliação pendente", metrics["clientes_com_conciliacao_pendente"]),
            ("Clientes com erro", metrics["clientes_com_erro"]),
            ("Transações", metrics["transacoes"]),
            ("Maior tempo", f"{metrics['maior_tempo_minutos']} min"),
        ]
    )
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(client['nome'])}</td>"
        f"<td>{html.escape(client['open_finance_status'])}</td>"
        f"<td>{'Sim' if client['puxou_extrato'] else 'Não'}</td>"
        f"<td>{client['transacoes']}</td>"
        f"<td>{client['a_classificar']}</td>"
        f"<td>{client['comprovantes_faltantes']}</td>"
        f"<td>{client['conciliacao_pendente']}</td>"
        f"<td>{client['tempo_total_minutos']} min</td>"
        f"<td><span class='badge'>{html.escape(client['status_geral'])}</span></td>"
        "</tr>"
        for client in status["clients"]
    )
    schedule_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row.get('descricao', ''))}</td>"
        f"<td>{html.escape(row.get('frequencia', ''))}</td>"
        f"<td>{html.escape(row.get('proxima_execucao', ''))}</td>"
        f"<td>{html.escape(row.get('ativo', ''))}</td>"
        "</tr>"
        for row in status["schedules"]
    )
    ready_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(client['nome'])}</td>"
        f"<td>{html.escape(client['cnpj'])}</td>"
        f"<td>{client['transacoes']}</td>"
        f"<td><code>{html.escape(client['client_id'])}_dominio.txt</code></td>"
        "</tr>"
        for client in status["clients"]
        if client["etapa_codigo"] == "pronto_dominio"
    )
    if not ready_rows:
        ready_rows = "<tr><td colspan='4'>Nenhum documento pronto neste processamento.</td></tr>"

    pending_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(client['nome'])}</td>"
        f"<td>{html.escape(client['status_geral'])}</td>"
        f"<td>{client['a_classificar']}</td>"
        f"<td>{client['comprovantes_faltantes']}</td>"
        f"<td>{client['conciliacao_pendente']}</td>"
        "</tr>"
        for client in status["clients"]
        if client["etapa_codigo"] != "pronto_dominio"
    )
    if not pending_rows:
        pending_rows = "<tr><td colspan='5'>Sem pendências neste processamento.</td></tr>"

    document = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Painel Contábil Open Finance</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; color: #172033; background: #f4f6f8; }}
    header {{ padding: 24px 32px; background: #ffffff; border-bottom: 1px solid #d9dee7; }}
    h1 {{ margin: 0; font-size: 24px; }}
    main {{ padding: 24px 32px; }}
    input[type="radio"] {{ position: absolute; opacity: 0; }}
    nav {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }}
    nav label {{ cursor: pointer; border: 1px solid #cfd6e1; background: #ffffff; border-radius: 8px; padding: 9px 12px; font-size: 13px; }}
    .panel {{ display: none; }}
    #tab-geral:checked ~ nav label[for="tab-geral"],
    #tab-clientes:checked ~ nav label[for="tab-clientes"],
    #tab-prontos:checked ~ nav label[for="tab-prontos"],
    #tab-pendencias:checked ~ nav label[for="tab-pendencias"],
    #tab-agenda:checked ~ nav label[for="tab-agenda"] {{ background: #164194; color: #ffffff; border-color: #164194; }}
    #tab-geral:checked ~ #geral,
    #tab-clientes:checked ~ #clientes,
    #tab-prontos:checked ~ #prontos,
    #tab-pendencias:checked ~ #pendencias,
    #tab-agenda:checked ~ #agenda {{ display: block; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .metric {{ background: #ffffff; border: 1px solid #d9dee7; border-radius: 8px; padding: 16px; }}
    .metric span {{ display: block; font-size: 12px; color: #667085; }}
    .metric strong {{ display: block; margin-top: 8px; font-size: 28px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; background: #ffffff; border: 1px solid #d9dee7; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e7ebf0; text-align: left; font-size: 13px; }}
    th {{ color: #475467; background: #f9fafb; }}
    h2 {{ margin-top: 28px; font-size: 18px; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 4px 8px; background: #edf2ff; color: #164194; font-size: 12px; }}
  </style>
</head>
<body>
  <header>
    <h1>Painel Contábil Open Finance</h1>
    <p>Atualizado em {html.escape(status['generated_at'])}</p>
  </header>
  <main>
    <input type="radio" id="tab-geral" name="tabs" checked>
    <input type="radio" id="tab-clientes" name="tabs">
    <input type="radio" id="tab-prontos" name="tabs">
    <input type="radio" id="tab-pendencias" name="tabs">
    <input type="radio" id="tab-agenda" name="tabs">
    <nav>
      <label for="tab-geral">Visão Geral</label>
      <label for="tab-clientes">Clientes</label>
      <label for="tab-prontos">Documentos Prontos</label>
      <label for="tab-pendencias">Pendências</label>
      <label for="tab-agenda">Agenda</label>
    </nav>
    <section id="geral" class="panel">
      <div class="grid">{cards}</div>
    </section>
    <section id="clientes" class="panel">
      <h2>Status por Cliente</h2>
      <table>
        <thead><tr><th>Cliente</th><th>Open Finance</th><th>Extrato</th><th>Transações</th><th>A classificar</th><th>Comprovantes</th><th>Conciliação</th><th>Tempo</th><th>Etapa</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <section id="prontos" class="panel">
      <h2>Documentos Prontos para Importar no Domínio</h2>
      <table>
        <thead><tr><th>Cliente</th><th>CNPJ</th><th>Transações</th><th>Arquivo TXT</th></tr></thead>
        <tbody>{ready_rows}</tbody>
      </table>
    </section>
    <section id="pendencias" class="panel">
      <h2>Pendências Operacionais</h2>
      <table>
        <thead><tr><th>Cliente</th><th>Status</th><th>A classificar</th><th>Comprovantes</th><th>Conciliação</th></tr></thead>
        <tbody>{pending_rows}</tbody>
      </table>
    </section>
    <section id="agenda" class="panel">
      <h2>Agenda</h2>
      <table>
        <thead><tr><th>Rotina</th><th>Frequência</th><th>Próxima execução</th><th>Ativo</th></tr></thead>
        <tbody>{schedule_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")
