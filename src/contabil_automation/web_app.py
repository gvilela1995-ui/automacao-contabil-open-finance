from __future__ import annotations

import csv
import html
import json
import mimetypes
import os
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.contabil_automation.apply_repeated_classification import build_batch_from_repeated
from src.contabil_automation.classification_review import write_repeated_csv, write_review_html
from src.contabil_automation.classifiers.batch_import import import_batch
from src.contabil_automation.connectors.bank_file_connector import load_bank_file, write_normalized_csv
from src.contabil_automation.xml_import import main as xml_import_main


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUTPUT = DATA / "output"
UPLOADS = DATA / "uploads"


def read_text(path: Path, default: str = "") -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else default


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [{key: value for key, value in row.items()} for row in csv.DictReader(file, delimiter=";")]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def parse_multipart(body: bytes, content_type: str) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    marker = "boundary="
    if marker not in content_type:
        return {}, {}
    boundary = ("--" + content_type.split(marker, 1)[1].strip().strip('"')).encode()
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}

    for part in body.split(boundary):
        part = part.strip()
        if not part or part == b"--":
            continue
        headers_blob, _, value = part.partition(b"\r\n\r\n")
        value = value.rstrip(b"\r\n-")
        headers = headers_blob.decode("utf-8", errors="ignore")
        name = ""
        filename = ""
        for section in headers.split(";"):
            section = section.strip()
            if section.startswith("name="):
                name = section.split("=", 1)[1].strip('"')
            elif section.startswith("filename="):
                filename = Path(section.split("=", 1)[1].strip('"')).name
        if not name:
            continue
        if filename:
            files[name] = (filename, value)
        else:
            fields[name] = value.decode("utf-8", errors="ignore").strip()
    return fields, files


def run_pipeline(input_file: str = "data/input/transacoes_upload.csv") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "src.contabil_automation.pipeline",
            "--input",
            input_file,
            "--clients",
            "data/input/clientes.csv",
            "--rules",
            "config/categorias.csv",
            "--domain-layout",
            "config/dominio_layout.json",
            "--conciliation",
            "data/input/conciliacao_exemplo.csv",
            "--schedules",
            "config/agendamentos.csv",
            "--stages",
            "config/etapas.csv",
            "--times",
            "data/input/tempos_cliente.csv",
            "--errors",
            "data/input/erros_coleta.csv",
            "--receipts-dir",
            "data/comprovantes",
            "--output-dir",
            "data/output",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def layout(message: str = "") -> str:
    status = read_csv(OUTPUT / "clientes_status.csv")
    consentimentos = read_csv(DATA / "input" / "consentimentos.csv")
    config = json.loads(read_text(ROOT / "config" / "automacao.json", "{}") or "{}")
    repeated = read_csv(OUTPUT / "classificacao_repetidos.csv")
    docs = sorted((OUTPUT / "documentos_prontos").glob("*")) if (OUTPUT / "documentos_prontos").exists() else []
    txt_preview = html.escape(read_text(OUTPUT / "lancamentos_dominio.txt"))
    cards = status_cards(status)
    client_rows = "\n".join(
        f"<tr><td>{h(row.get('nome'))}</td><td>{h(row.get('etapa_nome'))}</td><td>{h(row.get('transacoes'))}</td><td>{h(row.get('a_classificar'))}</td><td>{h(row.get('conciliacao_pendente'))}</td><td>{h(row.get('tempo_total_minutos'))} min</td></tr>"
        for row in status
    ) or "<tr><td colspan='6'>Rode um processamento para ver clientes.</td></tr>"
    consent_rows = "\n".join(
        f"<tr><td>{h(row.get('client_id'))}</td><td>{h(row.get('instituicao'))}</td><td>{h(row.get('tipo_conta'))}</td><td>{h(row.get('status'))}</td><td>{h(row.get('consent_id'))}</td><td>{h(row.get('expira_em'))}</td><td>{h(row.get('ultima_coleta'))}</td></tr>"
        for row in consentimentos
    ) or "<tr><td colspan='7'>Nenhum consentimento cadastrado.</td></tr>"
    repeated_rows = "\n".join(repeated_row(row, index) for index, row in enumerate(repeated))
    docs_rows = "\n".join(
        f"<tr><td>{h(path.name)}</td><td>{path.stat().st_size}</td><td><a href='/download?path={urllib.parse.quote(str(path.relative_to(ROOT)))}'>Abrir</a></td></tr>"
        for path in docs
        if path.is_file()
    ) or "<tr><td colspan='3'>Nenhum documento pronto ainda.</td></tr>"

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Automação Contábil</title>
  <style>
    body {{ margin:0; font-family: Arial, sans-serif; color:#172033; background:#f4f6f8; }}
    header {{ background:#fff; border-bottom:1px solid #d9dee7; padding:18px 24px; display:flex; justify-content:space-between; gap:16px; align-items:center; }}
    h1 {{ margin:0; font-size:22px; }} h2 {{ font-size:18px; margin:0 0 12px; }}
    main {{ padding:22px 24px; }}
    .tabs {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }}
    .tabs a {{ text-decoration:none; color:#172033; border:1px solid #cfd6e1; background:#fff; border-radius:8px; padding:9px 12px; font-size:13px; }}
    section {{ background:#fff; border:1px solid #d9dee7; border-radius:8px; padding:16px; margin-bottom:16px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; }}
    .metric {{ border:1px solid #e2e8f0; border-radius:8px; padding:12px; background:#fbfcfe; }}
    .metric span {{ color:#667085; font-size:12px; display:block; }} .metric strong {{ font-size:24px; display:block; margin-top:6px; }}
    table {{ width:100%; border-collapse:collapse; }} th,td {{ border-bottom:1px solid #e7ebf0; padding:9px; text-align:left; font-size:13px; vertical-align:top; }}
    th {{ background:#f9fafb; color:#475467; }}
    input,select {{ width:100%; box-sizing:border-box; padding:7px; border:1px solid #cfd6e1; border-radius:6px; }}
    button {{ border:0; background:#164194; color:#fff; border-radius:7px; padding:9px 12px; cursor:pointer; font-weight:600; }}
    .actions {{ display:flex; gap:8px; flex-wrap:wrap; }} .notice {{ background:#fff7e6; border-color:#ffd591; }}
    pre {{ background:#0f172a; color:#e5e7eb; padding:12px; border-radius:8px; overflow:auto; }}
  </style>
</head>
<body>
  <header>
    <div><h1>Automação Contábil</h1><small>Open Finance ou upload de OFX/CSV, classificação em lote e TXT Domínio</small></div>
    <form method="post" action="/processar"><button>Processar Tudo</button></form>
  </header>
  <main>
    {f"<section class='notice'>{h(message)}</section>" if message else ""}
    <nav class="tabs">
      <a href="#openfinance">Open Finance</a><a href="#upload">Upload</a><a href="#repetidos">Repetidos</a><a href="#clientes">Clientes</a><a href="#documentos">Documentos Prontos</a><a href="#txt">TXT</a>
    </nav>
    <section><div class="grid">{cards}</div></section>
    <section id="openfinance">
      <h2>Open Finance</h2>
      <div class="grid">
        <div class="metric"><span>Provider configurado</span><strong>{h(config.get('provider', 'csv'))}</strong></div>
        <div class="metric"><span>Base URL</span><strong>{h(config.get('base_url', 'pendente'))}</strong></div>
        <div class="metric"><span>Consentimentos</span><strong>{len(consentimentos)}</strong></div>
      </div>
      <p>Para produção, configure um agregador/API Open Finance e mantenha os consentimentos ativos. Senha bancária do cliente não entra no sistema.</p>
      <form method="post" action="/coletar-open-finance" class="actions">
        <button>Coletar Open Finance</button>
        <button formaction="/modo-open-finance">Ativar provider open_finance</button>
        <button formaction="/modo-upload">Usar provider csv/upload</button>
      </form>
      <table>
        <thead><tr><th>Cliente</th><th>Instituição</th><th>Tipo</th><th>Status</th><th>Consent ID</th><th>Expira</th><th>Última coleta</th></tr></thead>
        <tbody>{consent_rows}</tbody>
      </table>
    </section>
    <section id="upload">
      <h2>Importar Extrato sem Open Finance</h2>
      <form method="post" action="/upload" enctype="multipart/form-data">
        <div class="grid">
          <label>Cliente <input name="client_id" value="cliente_teste"></label>
          <label>Conta <input name="account_id" value="conta_manual"></label>
          <label>Arquivo OFX/CSV <input name="file" type="file" accept=".ofx,.csv,.txt"></label>
        </div><br>
        <button>Importar Extrato</button>
      </form>
    </section>
    <section id="repetidos">
      <h2>Classificação por Nomes Repetidos</h2>
      <form method="post" action="/gerar-repetidos" class="actions"><button>Atualizar Repetidos</button></form>
      <form method="post" action="/aplicar-repetidos">
        <table>
          <thead><tr><th>Aplicar?</th><th>Descrição</th><th>Qtd</th><th>Débito</th><th>Crédito</th><th>Cód. Histórico</th><th>Histórico</th></tr></thead>
          <tbody>{repeated_rows or "<tr><td colspan='7'>Nenhum repetido gerado ainda.</td></tr>"}</tbody>
        </table><br>
        <button>Aplicar Classificações Marcadas</button>
      </form>
    </section>
    <section id="clientes">
      <h2>Etapas por Cliente</h2>
      <table><thead><tr><th>Cliente</th><th>Etapa</th><th>Lançamentos</th><th>A classificar</th><th>Conciliação</th><th>Tempo</th></tr></thead><tbody>{client_rows}</tbody></table>
    </section>
    <section id="documentos">
      <h2>Documentos Prontos</h2>
      <table><thead><tr><th>Arquivo</th><th>Tamanho</th><th>Ação</th></tr></thead><tbody>{docs_rows}</tbody></table>
    </section>
    <section id="txt">
      <h2>Prévia TXT Domínio</h2>
      <pre>{txt_preview}</pre>
    </section>
  </main>
</body>
</html>"""


def h(value: object) -> str:
    return html.escape(str(value or ""))


def status_cards(rows: list[dict[str, str]]) -> str:
    total = len(rows)
    pronto = len([row for row in rows if row.get("etapa_codigo") == "pronto_dominio"])
    classificar = len([row for row in rows if row.get("etapa_codigo") == "classificar"])
    conciliar = len([row for row in rows if row.get("etapa_codigo") == "conciliar"])
    transacoes = sum(int(row.get("transacoes") or 0) for row in rows)
    return "".join(
        f"<div class='metric'><span>{label}</span><strong>{value}</strong></div>"
        for label, value in [
            ("Clientes", total),
            ("Prontos", pronto),
            ("Classificar", classificar),
            ("Conciliar", conciliar),
            ("Lançamentos", transacoes),
        ]
    )


def repeated_row(row: dict[str, str], index: int) -> str:
    checked = "checked" if (row.get("aplicar_mesma_classificacao") or "").lower() in {"sim", "s", "true", "1"} else ""
    return f"""<tr>
      <td><input type="checkbox" name="apply_{index}" {checked}><input type="hidden" name="descricao_{index}" value="{h(row.get('descricao_repetida'))}"></td>
      <td>{h(row.get('descricao_repetida'))}</td>
      <td>{h(row.get('quantidade'))}</td>
      <td><input name="debito_{index}" value="{h(row.get('conta_debito'))}"></td>
      <td><input name="credito_{index}" value="{h(row.get('conta_credito'))}"></td>
      <td><input name="codigo_{index}" value="{h(row.get('codigo_historico'))}"></td>
      <td><input name="historico_{index}" value="{h(row.get('historico_padrao'))}"></td>
    </tr>"""


class Handler(BaseHTTPRequestHandler):
    def send_html(self, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect_home(self, message: str) -> None:
        self.send_html(layout(message))

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/download":
            query = urllib.parse.parse_qs(parsed.query)
            rel = query.get("path", [""])[0]
            path = (ROOT / rel).resolve()
            if not str(path).startswith(str(ROOT)) or not path.exists():
                self.send_error(404)
                return
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_html(layout())

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/upload":
            fields, files = parse_multipart(body, self.headers.get("Content-Type", ""))
            filename, content = files.get("file", ("", b""))
            if not filename:
                self.redirect_home("Selecione um arquivo OFX ou CSV.")
                return
            UPLOADS.mkdir(parents=True, exist_ok=True)
            saved = UPLOADS / filename
            saved.write_bytes(content)
            transactions = load_bank_file(saved, fields.get("client_id", "cliente_teste"), fields.get("account_id", "conta_manual"))
            write_normalized_csv(DATA / "input" / "transacoes_upload.csv", transactions)
            self.redirect_home(f"Extrato importado: {len(transactions)} lançamento(s).")
            return

        form = urllib.parse.parse_qs(body.decode("utf-8", errors="ignore"))
        if parsed.path == "/gerar-repetidos":
            write_repeated_csv(OUTPUT / "classificacao_repetidos.csv", DATA / "input" / "transacoes_upload.csv", ROOT / "config" / "categorias.csv")
            write_review_html(OUTPUT / "classificacao_repetidos.html", OUTPUT / "classificacao_repetidos.csv")
            self.redirect_home("Repetidos atualizados.")
            return
        if parsed.path == "/aplicar-repetidos":
            rows = []
            indexes = sorted({key.split("_", 1)[1] for key in form if key.startswith("descricao_")}, key=int)
            for index in indexes:
                rows.append(
                    {
                        "descricao_repetida": form.get(f"descricao_{index}", [""])[0],
                        "categoria_atual": "Classificado pelo escritório",
                        "conta_debito": form.get(f"debito_{index}", [""])[0],
                        "conta_credito": form.get(f"credito_{index}", [""])[0],
                        "codigo_historico": form.get(f"codigo_{index}", [""])[0],
                        "historico_padrao": form.get(f"historico_{index}", [""])[0],
                        "aplicar_mesma_classificacao": "sim" if f"apply_{index}" in form else "nao",
                    }
                )
            repeated = OUTPUT / "classificacao_repetidos.csv"
            write_csv(
                repeated,
                rows,
                ["descricao_repetida", "categoria_atual", "conta_debito", "conta_credito", "codigo_historico", "historico_padrao", "aplicar_mesma_classificacao"],
            )
            batch = OUTPUT / "classificacao_repetidos_aprovadas.csv"
            build_batch_from_repeated(repeated, batch)
            import_batch(batch, ROOT / "config" / "categorias.csv")
            run_pipeline()
            self.redirect_home("Classificações aplicadas e arquivos reprocessados.")
            return
        if parsed.path == "/processar":
            result = run_pipeline()
            self.redirect_home("Processamento concluído." if result.returncode == 0 else result.stderr)
            return
        if parsed.path == "/coletar-open-finance":
            result = subprocess.run(
                [sys.executable, "-m", "src.contabil_automation.automatic_runner", "--config", "config/automacao.json"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            message = result.stdout if result.returncode == 0 else (result.stdout + "\n" + result.stderr)
            self.redirect_home(message)
            return
        if parsed.path in {"/modo-open-finance", "/modo-upload"}:
            config_path = ROOT / "config" / "automacao.json"
            config = json.loads(read_text(config_path, "{}") or "{}")
            config["provider"] = "open_finance" if parsed.path == "/modo-open-finance" else "csv"
            config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            self.redirect_home(f"Provider alterado para {config['provider']}.")
            return
        self.send_error(404)


def main() -> int:
    host = os.environ.get("APP_HOST", "127.0.0.1")
    port = int(os.environ.get("APP_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Sistema aberto em http://{host}:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
