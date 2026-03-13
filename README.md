# CSVtoSEPAXML

Python-Projekt zur Erzeugung von SEPA Credit Transfer XML im Format `pain.001.001.09` aus CSV-Dateien.

## Unterstütztes CSV-Format (v1)

Minimales Eingangsschema (Semikolon-getrennt):

```csv
Name;Verwendungszweck;Betrag;IBAN;BIC
```

- `Name` → Empfängername (`Cdtr/Nm`)
- `Verwendungszweck` → `RmtInf/Ustrd`
- `Betrag` → `Amt/InstdAmt` (deutsches Dezimalkomma, z. B. `24,00`)
- `IBAN` → Empfänger-IBAN (`CdtrAcct/Id/IBAN`)
- `BIC` → optional (`CdtrAgt/FinInstnId/BICFI`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e .[dev]
```

Optional für XSD-Validierung:

```bash
pip install -e .[xml]
```

## Konfiguration

Interaktiv:

```bash
csv-to-sepa init-config config.json
```

Oder Vorlage nutzen: `examples/config.example.json`.

## CSV vorab validieren

```bash
csv-to-sepa validate-csv config.json examples/input_minimal.csv
```

## XML erzeugen

```bash
csv-to-sepa convert config.json examples/input_minimal.csv output.xml
```

Optionales Ausführungsdatum überschreiben:

```bash
csv-to-sepa convert config.json examples/input_minimal.csv output.xml --execution-date 2026-03-16
```

## XML gegen XSD validieren (optional)

```bash
csv-to-sepa validate-xml output.xml pain.001.001.09.xsd
```

## Tests

```bash
pytest -q
```

## Hinweise zur Bankkompatibilität

- Ziel ist ein robustes, minimales SCT-Profil (`PmtMtd=TRF`, `SvcLvl=SEPA`, `ChrgBr=SLEV`).
- BIC ist optional; wenn vorhanden wird er validiert und ausgegeben.
- Vor produktivem Einsatz sollte die Datei immer mit den bankeigenen MIG-/Upload-Prüfungen getestet werden.
