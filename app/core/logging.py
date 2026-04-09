import logging
from logging.config import dictConfig


def setup_logging(level: str = "INFO") -> None:
    normalized_level = level.upper()

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": normalized_level,
                }
            },
            "loggers": {
                "": {"handlers": ["default"], "level": normalized_level},
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": normalized_level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": normalized_level,
                    "propagate": False,
                },
            },
        }
    )

    logging.getLogger(__name__).debug("Logging configured")
