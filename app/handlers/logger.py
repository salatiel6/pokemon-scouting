"""
Basic logging, centralized so sinks/other logging necessities can be customized centrally
"""

import logging

# Define ANSI escape codes for colors
RESET = "\033[0m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[93m"
RED = "\033[31m"
WHITE_BG_RED = "\033[41m\033[97m"

COLORS = {
    "INFO": GREEN,
    "DEBUG": BLUE,
    "WARNING": YELLOW,
    "ERROR": RED,
    "CRITICAL": WHITE_BG_RED,
}


class CustomFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a log record with color based on its severity level.

        This method overrides the base formatters `format` method to apply
        color codes to the log message, making it visually distinguishable
        based on the log level.

        :param record: The log record to be formatted.
        :return: The formatted log message with appropriate color codes applied.
        """
        log_color = COLORS.get(record.levelname, RESET)
        message = super().format(record)
        return f"{log_color}{message}{RESET}"


# Define the log format
log_format = "%(funcName)s | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"


# Create a console handler and set the custom formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter(log_format, datefmt=date_format))

# Create the logger
logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.propagate = False

if __name__ == "__main__":
    logger.info("Info logging test")
    logger.debug("Debug logging test")
    logger.warning("Warning logging test")
    logger.error("Error logging test")
    logger.critical("Critical logging test")
