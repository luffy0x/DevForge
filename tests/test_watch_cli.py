from devforge import watch_cli


def test_watch_once_delegates_to_scan(monkeypatch) -> None:
    calls = []

    def fake_scan(argv):
        calls.append(argv)
        return 0

    monkeypatch.setattr(watch_cli, "scan_main", fake_scan)
    assert watch_cli.main(["--once", "--github-repository", "acme/app"]) == 0
    assert calls == [["--github-repository", "acme/app"]]
