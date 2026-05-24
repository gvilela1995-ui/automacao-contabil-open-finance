from __future__ import annotations

import argparse
from pathlib import Path

from src.contabil_automation.connectors.bank_file_connector import load_bank_file, write_normalized_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa OFX/CSV bancario para o formato interno do sistema.")
    parser.add_argument("--file", required=True, help="Arquivo OFX ou CSV bancario.")
    parser.add_argument("--client-id", required=True, help="ID do cliente no sistema.")
    parser.add_argument("--account-id", default="conta_manual", help="ID interno da conta.")
    parser.add_argument("--output", default="data/input/transacoes_upload.csv", help="CSV normalizado de saida.")
    args = parser.parse_args()

    transactions = load_bank_file(Path(args.file), args.client_id, args.account_id)
    write_normalized_csv(Path(args.output), transactions)
    print(f"Transacoes importadas: {len(transactions)}")
    print(f"Arquivo normalizado: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
