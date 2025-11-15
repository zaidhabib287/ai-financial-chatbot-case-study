import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from backend.config.settings import settings


def setup_logger(name: str = __name__) -> logging.Logger:
    """Setup logger with both file and console handlers"""

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_path = Path(settings.log_file)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10485760, backupCount=5  # 10MB
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logger("financial_chatbot")
