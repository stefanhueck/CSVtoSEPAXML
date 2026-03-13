import argparse

from csv_to_sepa.cli import cmd_init_config


def test_cmd_init_config_prints_next_steps(monkeypatch, capsys, tmp_path) -> None:
    output_file = tmp_path / "config.json"

    inputs = iter(
        [
            "Example Org",
            "DE89370400440532013000",
            "",
            "",
            "",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    args = argparse.Namespace(output=str(output_file), language="en")
    cmd_init_config(args)

    stdout = capsys.readouterr().out
    assert "Config written to" in stdout
    assert "Next steps:" in stdout
    assert "csv-to-sepa validate-csv" in stdout
    assert "csv-to-sepa convert" in stdout
    assert "README.md" in stdout


def test_cmd_init_config_prints_next_steps_de(monkeypatch, capsys, tmp_path) -> None:
    output_file = tmp_path / "config_de.json"

    inputs = iter(
        [
            "Beispiel Verein",
            "DE89370400440532013000",
            "",
            "",
            "",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    args = argparse.Namespace(output=str(output_file), language="de")
    cmd_init_config(args)

    stdout = capsys.readouterr().out
    assert "Konfiguration wurde geschrieben" in stdout
    assert "Nächste Schritte:" in stdout
    assert "README.md" in stdout
