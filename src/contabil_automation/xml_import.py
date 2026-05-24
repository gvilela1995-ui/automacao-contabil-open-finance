from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from pathlib import Path


def text(root: ET.Element, path: str) -> str:
    found = root.find(path)
    return (found.text or "").strip() if found is not None and found.text else ""


def strip_namespace(tree: ET.ElementTree) -> ET.Element:
    root = tree.getroot()
    for element in root.iter():
        if "}" in element.tag:
            element.tag = element.tag.split("}", 1)[1]
    return root


def parse_xml(path: Path) -> dict[str, str]:
    root = strip_namespace(ET.parse(path))
    inf = root.find(".//infNFe")
    chave = ""
    if inf is not None:
        chave = (inf.attrib.get("Id") or "").replace("NFe", "")
    return {
        "arquivo": path.name,
        "chave": chave,
        "numero": text(root, ".//ide/nNF"),
        "emissao": text(root, ".//ide/dhEmi")[:10] or text(root, ".//ide/dEmi")[:10],
        "emitente_cnpj": text(root, ".//emit/CNPJ") or text(root, ".//emit/CPF"),
        "emitente_nome": text(root, ".//emit/xNome"),
        "destinatario_cnpj": text(root, ".//dest/CNPJ") or text(root, ".//dest/CPF"),
        "destinatario_nome": text(root, ".//dest/xNome"),
        "valor": text(root, ".//ICMSTot/vNF"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa XML de NFe/NFCe para apoio de conciliacao.")
    parser.add_argument("--xml-dir", default="data/xml", help="Pasta com XMLs.")
    parser.add_argument("--output", default="data/output/xml_resumo.csv", help="CSV de resumo dos XMLs.")
    args = parser.parse_args()

    xml_dir = Path(args.xml_dir)
    rows = [parse_xml(path) for path in sorted(xml_dir.glob("*.xml"))] if xml_dir.exists() else []
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["arquivo", "chave", "numero", "emissao", "emitente_cnpj", "emitente_nome", "destinatario_cnpj", "destinatario_nome", "valor"],
            delimiter=";",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"XMLs importados: {len(rows)}")
    print(f"Resumo: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
