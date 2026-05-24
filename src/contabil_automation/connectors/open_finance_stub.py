from __future__ import annotations

from pathlib import Path


class OpenFinanceNotConfigured(RuntimeError):
    pass


def fetch_transactions(output_csv: Path) -> Path:
    raise OpenFinanceNotConfigured(
        "Conector Open Finance real ainda nao configurado. "
        "Defina um provedor/agregador autorizado, credenciais e consentimentos dos clientes."
    )
