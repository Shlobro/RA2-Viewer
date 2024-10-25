import logging
import sys


def setup_logging(log_to_console=True):
    """
    Sets up logging for the application. Outputs to the console by default.
    To switch to file logging, set log_to_console=False.
    """
    # Common logging format
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    if log_to_console:
        # Console handler setup
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))

        logging.basicConfig(
            level=logging.INFO,  # Adjust the level as needed
            handlers=[console_handler],
            format=log_format
        )
    else:
        # File handler setup (for fast, buffered logging to file)
        file_handler = logging.FileHandler('app.log', delay=True)  # Delay means file is opened only when needed
        file_handler.setFormatter(logging.Formatter(log_format))

        logging.basicConfig(
            level=logging.DEBUG,  # Adjust the level as needed
            handlers=[file_handler],
            format=log_format
        )

    logging.info("Logging setup complete")
