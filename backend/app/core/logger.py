"""Logging configuration"""

import logging
import sys
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with proper configuration"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


def get_app_logger() -> logging.Logger:
    """Get the main application logger"""
    global _logger
    if _logger is None:
        _logger = get_logger("mongodb_to_csv")
    return _logger
