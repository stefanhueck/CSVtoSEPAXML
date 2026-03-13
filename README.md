# CSVtoSEPAXML

Python project to generate SEPA Credit Transfer XML in `pain.001.001.09` format from CSV files.

## Supported CSV format (v1)

Minimal input schema (semicolon-separated):

```csv
Name;Verwendungszweck;Betrag;IBAN;BIC
```

- `Name` → creditor name (`Cdtr/Nm`)
- `Verwendungszweck` → `RmtInf/Ustrd`
- `Betrag` → `Amt/InstdAmt` (German decimal comma, e.g. `24,00`)
- `IBAN` → creditor IBAN (`CdtrAcct/Id/IBAN`)
- `BIC` → optional (`CdtrAgt/FinInstnId/BICFI`)

Equivalent English minimal headers are also supported:

```csv
CreditorName;RemittanceInformation;Amount;CreditorIBAN;CreditorBIC
```

Extended input schema (backward compatible):

```csv
Name;Verwendungszweck;Betrag;IBAN;BIC;EndToEndId;ExecutionDate;PurposeCode
```

- `EndToEndId` (optional): custom value instead of auto-generated ID
- `ExecutionDate` (optional): row-level execution date `YYYY-MM-DD`
- `PurposeCode` (optional): 4-character code (e.g. `SALA`, `TRAD`)

English aliases are accepted for all key columns, including extended fields.
This means real-world CSVs with either German or English header labels can be parsed.

Backward compatibility:

- If extended columns are missing, minimal CSV continues to work unchanged.
- `ExecutionDate` is then taken from CLI `--execution-date` or config default.
- If multiple `ExecutionDate` values are present, the generator creates multiple `PmtInf` blocks automatically.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m pip install '.[dev]'
```

Optional for XSD validation:

```bash
python -m pip install '.[xml]'
```

Optional (editable install for local development):

```bash
python -m pip install -e .
python -m pip install -e '.[dev]'
```

Note: On Python 3.13, editable installs can fail in some environments (module import errors from hidden `__editable__*.pth` files). If that happens, use the non-editable commands above.

## Configuration

Interactive setup:

```bash
csv-to-sepa init-config config.json
```

Language (English by default, optional German):

```bash
csv-to-sepa init-config config.json --language en
csv-to-sepa init-config config.json --language de
```

Inputs are validated immediately. Invalid values display a helpful message and the same prompt is shown again (e.g. invalid IBAN/BIC/date).

- `default_execution_date` is optional; if empty, today’s date is used automatically.
- `charge_bearer` is optional; if empty, `SLEV` is used.

After successful setup, the command prints the expected next steps for CSV validation and conversion, plus a README hint.

Or use the template file: `examples/config.example.json`.

## Create CSV templates

Minimal template:

```bash
csv-to-sepa create-template template_minimal.csv --mode minimal
```

By default, generated template headers are English.

Generate template headers in English:

```bash
csv-to-sepa create-template template_minimal_en.csv --mode minimal --template-header-language en
```

Generate template headers in German:

```bash
csv-to-sepa create-template template_minimal_de.csv --mode minimal --template-header-language de
```

Switch output language:

```bash
csv-to-sepa create-template template_minimal.csv --mode minimal --language de
```

You can combine both options, for example German output messages with English template headers:

```bash
csv-to-sepa create-template template_extended_en.csv --mode extended --template-header-language en --language de
```

Extended template:

```bash
csv-to-sepa create-template template_extended.csv --mode extended
```

## Validate CSV before conversion

```bash
csv-to-sepa validate-csv config.json examples/input_minimal.csv
```

```bash
csv-to-sepa validate-csv config.json examples/input_minimal.csv --language de
```

On errors, the CLI prints actionable diagnostics (for example row/field/cause) instead of only failing with a generic exception.

## Generate XML

```bash
csv-to-sepa convert config.json examples/input_minimal.csv output.xml
```

```bash
csv-to-sepa convert config.json examples/input_minimal.csv output.xml --language de
```

Conversion also prints detailed validation and parsing errors to make CSV fixes faster.

Use extended CSV:

```bash
csv-to-sepa convert config.json examples/input_extended.csv output_extended.xml
```

Override execution date:

```bash
csv-to-sepa convert config.json examples/input_minimal.csv output.xml --execution-date 2026-03-16
```

## Validate XML against XSD (optional)

```bash
csv-to-sepa validate-xml output.xml pain.001.001.09.xsd
```

```bash
csv-to-sepa validate-xml output.xml pain.001.001.09.xsd --language de
```

If the XML or XSD path is wrong, the CLI now prints a clear file-not-found
message including the resolved path.

For missing XSD files, the CLI additionally prints a direct recovery hint with
an example path usage.

Recommended project setup:

- Store XSD files in a versioned project folder such as `./xsd/`.
- Run validation with a stable path, for example:

```bash
csv-to-sepa validate-xml output.xml ./xsd/pain.001.001.09.xsd
```

Recommended placement for your EPC package files:

- `./xsd/EPC132-08_2025_V1.0_pain.001.001.09.xsd` (primary XSD for this project)
- `./xsd/EPC132-08_2025_V1.0_pain.002.001.10.xsd` (optional, for status-report scenarios)
- `./docs/epc/EPC132-08_2025_V1.0_pain.001.001.09_ERI` (optional reference doc)
- `./docs/epc/EPC132-08_2025_V1.0_pain.001.001.09_TB` (optional reference doc)

Optional convenience copy for shorter commands:

- `./xsd/pain.001.001.09.xsd` (copy or symlink to the EPC `.xsd` file)

Use the helper command to detect namespace and get suggested XSD filenames from an XML file:

```bash
csv-to-sepa check-namespace output.xml
```

Where to get the XSD online:

- EPC SCT C2PSP Implementation Guidelines page (includes XSD downloads):
	`https://www.europeanpaymentscouncil.eu/document-library/implementation-guidelines/sepa-credit-transfer-customer-psp-implementation-1`
- ISO 20022 message catalogue download page for Payments Initiation (`pain`):
	`https://www.iso20022.org/business-area/81/download`

## Tests

```bash
pytest -q
```

## Bank compatibility notes

- Target profile is a robust minimal SCT setup (`PmtMtd=TRF`, `SvcLvl=SEPA`, `ChrgBr=SLEV`).
- BIC is optional; when provided, it is validated and written to XML.
- Before production use, always verify files with your bank’s own MIG/upload checks.
