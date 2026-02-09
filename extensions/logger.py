from enum import Enum
from datetime import datetime
from pathlib import Path
from config import LOG_DIR


class LogType(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Logger:
    """
    Logger class for handling application logging.
    Logs are written to daily log files in the specified log directory.
    Each log entry includes a timestamp, log level, and message.
    """

    def __init__(self, log_dir: Path = LOG_DIR) -> None:
        self.log_dir = log_dir
        self._ensure_log_directory_exists()

    def _ensure_log_directory_exists(self) -> None:
        # Create the log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_today_logfile(self) -> Path:
        # Generate the log file name based on the current date (e.g., "2024-06-01.log")
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"rag_llm_{date_str}.log"

    def _print_to_file(self, message: str, filename: Path) -> None:
        # Append the log message to the specified log file
        with open(filename, "a", encoding="utf-8") as f:
            f.write(message + "\n")

    def _log(self, message: str, type: LogType) -> None:
        # Format the log message with a timestamp and log level, then write it to the daily log file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{type.value}] {message}"
        self._print_to_file(line, self._get_today_logfile())

    def log_error(self, error_message: str) -> None:
        self._log(error_message, LogType.ERROR)

    def log_warning(self, warning_message: str) -> None:
        self._log(warning_message, LogType.WARNING)

    def log_info(self, info_message: str) -> None:
        self._log(info_message, LogType.INFO)
