"""
Structured logging configuration using loguru.
Sets up separate log files for different components and console logging.
"""

import sys
from pathlib import Path
from loguru import logger
from config import settings

def setup_logging():
    """Configure loguru logging with multiple sinks."""
    # Remove default handler
    logger.remove()
    
    log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}"
    log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
    
    # Console logger
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=True
    )
    
    # File loggers
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    common_args = {
        "format": log_format,
        "rotation": "10 MB",
        "retention": "7 days",
        "compression": "zip",
        "enqueue": True
    }
    
    # Application log (everything)
    logger.add(
        log_dir / "application.log",
        level=log_level,
        **common_args
    )
    
    # Broker log (API calls, orders)
    logger.add(
        log_dir / "broker.log",
        level="DEBUG",
        filter=lambda record: "broker" in record["name"].lower(),
        **common_args
    )
    
    # Model log (training, predictions)
    logger.add(
        log_dir / "model.log",
        level="DEBUG",
        filter=lambda record: "model" in record["name"].lower() or "ml" in record["name"].lower(),
        **common_args
    )
    
    # Errors log
    logger.add(
        log_dir / "errors.log",
        level="ERROR",
        **common_args
    )

# Setup on import
setup_logging()

def get_logger(name: str):
    """
    Get a bound logger for a specific module.
    
    Args:
        name: The module name (__name__)
        
    Returns:
        A loguru logger instance bound to the given name.
    """
    return logger.bind(name=name)
