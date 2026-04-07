from datetime import datetime as py_datetime
from application import logger as logger_module


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

def test_print_to_file_appends_without_overwrite(tmp_path) -> None:
    """_print_to_file should append to an existing file instead of overwriting."""
    logger = logger_module.Logger(log_dir=tmp_path)
    logfile = tmp_path / "custom.log"
    logfile.write_text("first\n", encoding="utf-8")

    logger._print_to_file("second", logfile)

    assert logfile.read_text(encoding="utf-8").splitlines() == ["first", "second"]

def test_logger_creates_log_directory_as_directory(tmp_path) -> None:
    """Logger should create log directory and it must be a directory."""
    log_dir = tmp_path / "logs"
    logger_module.Logger(log_dir=log_dir)
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_log_appends_multiple_info_lines(tmp_path, monkeypatch) -> None:
    """Multiple log_info calls should append (not overwrite) within same daily file."""
    _patch_datetime(monkeypatch)
    logger = logger_module.Logger(log_dir=tmp_path)

    logger.log_info("one")
    logger.log_info("two")

    logfile = tmp_path / "rag_llm_2026-02-08.log"
    assert logfile.read_text(encoding="utf-8").splitlines() == [
        "[2026-02-08 13:14:15] [INFO] one",
        "[2026-02-08 13:14:15] [INFO] two",
    ]


def test__log_writes_given_level(tmp_path, monkeypatch) -> None:
    """_log should respect the provided LogType (direct private method test)."""
    _patch_datetime(monkeypatch)
    logger = logger_module.Logger(log_dir=tmp_path)

    logger._log("x", logger_module.LogType.ERROR)

    logfile = tmp_path / "rag_llm_2026-02-08.log"
    assert logfile.read_text(encoding="utf-8").splitlines() == [
        "[2026-02-08 13:14:15] [ERROR] x"
    ]
