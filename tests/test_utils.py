import signal
import functools
import logging
import sys


def configure_logging():
    """Configure logging to output to stdout with debug level enabled."""
    # Configure logging to output to stdout
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to avoid duplicate output
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create a stream handler that outputs to stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)

    # Create a formatter with more detailed output
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stream_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(stream_handler)

    # Force immediate flushing of logs
    stream_handler.flush = lambda: None


def timeout(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"Test timed out after {seconds} seconds")

            # Set the signal handler and a 10-second alarm
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)

            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm
                signal.alarm(0)
            return result

        return wrapper

    return decorator
