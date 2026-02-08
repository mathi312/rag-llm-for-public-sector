from datetime import datetime as py_datetime
from extensions import logger as logger_module


class FixedDateTime:
    @classmethod
    def now(cls) -> py_datetime:
        return py_datetime(2026, 2, 8, 13, 14, 15)


def _patch_datetime(monkeypatch) -> None:
    monkeypatch.setattr(logger_module, "datetime", FixedDateTime)


def test_logger_creates_log_directory(tmp_path) -> None:
    """Logger should create the log directory on initialization."""
    log_dir = tmp_path / "logs"
    assert not log_dir.exists()

    logger_module.Logger(log_dir=log_dir)

    assert log_dir.exists()


def test_get_today_logfile_uses_current_date(tmp_path, monkeypatch) -> None:
    """Logfile naming should include the fixed date in the expected format."""
    _patch_datetime(monkeypatch)
    log_dir = tmp_path / "logs"
    logger = logger_module.Logger(log_dir=log_dir)

    logfile = logger._get_today_logfile()

    assert logfile == log_dir / "rag_llm_2026-02-08.log"


def test_log_info_writes_expected_format(tmp_path, monkeypatch) -> None:
    """log_info should write a single formatted INFO line to the daily log file."""
    _patch_datetime(monkeypatch)
    logger = logger_module.Logger(log_dir=tmp_path)

    logger.log_info("hello")

    logfile = tmp_path / "rag_llm_2026-02-08.log"
    assert logfile.exists()
    assert (
        logfile.read_text(encoding="utf-8").strip()
        == "[2026-02-08 13:14:15] [INFO] hello"
    )


def test_log_warning_and_error_append_lines(tmp_path, monkeypatch) -> None:
    """log_warning/log_error should append lines in order with correct levels."""
    _patch_datetime(monkeypatch)
    logger = logger_module.Logger(log_dir=tmp_path)

    logger.log_warning("warn")
    logger.log_error("boom")

    logfile = tmp_path / "rag_llm_2026-02-08.log"
    lines = logfile.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "[2026-02-08 13:14:15] [WARNING] warn",
        "[2026-02-08 13:14:15] [ERROR] boom",
    ]
