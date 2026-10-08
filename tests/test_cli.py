import json

from ossnet.cli import main

PEOPLE = [f"Dev {i} <dev{i}@example.org>" for i in range(6)]


def build_project(repo):
    """Two maintainers for three years, plus a stream of newcomers."""
    for day in range(0, 3 * 365, 20):
        repo.commit(PEOPLE[0], day, write=["core.py"])
        repo.commit(PEOPLE[1], day + 3, write=["core.py", "util.py"])
    for i, person in enumerate(PEOPLE[2:]):
        start = 100 + i * 150
        repo.commit(person, start, write=["core.py" if i % 2 else f"docs/page{i}.md"])
        if i % 2:
            repo.commit(person, start + 450, write=["core.py"])


def test_cli_writes_report_and_data(repo, tmp_path, capsys):
    build_project(repo)
    out = tmp_path / "out"
    assert main([str(repo.path), "-o", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "Truck factor" in printed and "Newcomers who stayed" in printed
    for name in ("report.html", "summary.json", "timeline.csv", "contributors.csv", "newcomers.csv"):
        assert (out / name).stat().st_size > 0

    summary = json.loads((out / "summary.json").read_text())
    assert summary["history"]["people"] == 6
    assert summary["current"]["knowledge"]["truck_factor"] >= 1
    assert {"Dev 0", "Dev 1"} <= set(summary["current"]["core_80"])
    html = (out / "report.html").read_text()
    assert "<script type=\"application/json\" id=\"ossnet-data\">" in html


def test_cli_reports_git_errors(tmp_path, capsys):
    assert main([str(tmp_path)]) == 1
    assert "ossnet:" in capsys.readouterr().err
