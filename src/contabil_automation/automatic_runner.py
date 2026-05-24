from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from src.contabil_automation.connectors.open_finance_stub import OpenFinanceNotConfigured, fetch_transactions


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def log(message: str, log_path: Path) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}"
    print(line)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as file:
        file.write(line + "\n")


def run_pipeline(config: dict, input_csv: Path, log_path: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "src.contabil_automation.pipeline",
        "--input",
        str(input_csv),
        "--clients",
        config["clients_csv"],
        "--rules",
        config["rules_csv"],
        "--domain-layout",
        config["domain_layout"],
        "--conciliation",
        config["conciliation_csv"],
        "--schedules",
        config["schedules_csv"],
        "--stages",
        config["stages_csv"],
        "--times",
        config["times_csv"],
        "--errors",
        config["errors_csv"],
        "--receipts-dir",
        config["receipts_dir"],
        "--output-dir",
        config["output_dir"],
    ]
    log("Executando pipeline contabil.", log_path)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.stdout:
        log(result.stdout.strip(), log_path)
    if result.stderr:
        log(result.stderr.strip(), log_path)
    if result.returncode != 0:
        raise RuntimeError(f"Pipeline falhou com codigo {result.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Execucao automatica Open Finance -> Dominio.")
    parser.add_argument("--config", default="config/automacao.json", help="Arquivo de configuracao da automacao.")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    log_dir = Path(config.get("log_dir", "logs"))
    log_path = log_dir / f"execucao-{datetime.now().strftime('%Y%m%d')}.log"
    provider = (config.get("provider") or "csv").strip().lower()

    log(f"Iniciando automacao. Provider={provider}", log_path)

    if provider == "csv":
        input_csv = Path(config["input_csv"])
        log(f"Modo CSV de teste. Entrada={input_csv}", log_path)
    elif provider == "open_finance":
        try:
            input_csv = fetch_transactions(Path(config.get("input_csv", "data/input/transacoes_open_finance.csv")))
            log(f"Transacoes Open Finance salvas em {input_csv}", log_path)
        except OpenFinanceNotConfigured as error:
            log(str(error), log_path)
            return 2
    else:
        log(f"Provider desconhecido: {provider}", log_path)
        return 2

    run_pipeline(config, input_csv, log_path)
    log("Automacao concluida com sucesso.", log_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
