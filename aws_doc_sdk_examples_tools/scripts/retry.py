import logging
from functools import wraps
import random
import time
from typing import Callable, Type, Tuple

logger = logging.getLogger(__name__)


def retry_with_backoff(
    exceptions: Tuple[Type[Exception], ...],
    max_retries: int = 5,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: float = 0.1,
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff upon specified exceptions.

    :param exceptions: Tuple of exception classes to catch.
    :param max_retries: Maximum number of retry attempts.
    :param initial_delay: Initial delay between retries in seconds.
    :param backoff_factor: Factor by which the delay increases after each retry.
    :param max_delay: Maximum delay between retries in seconds.
    :param jitter: Random jitter added to delay to prevent thundering herd problem.
    :return: Decorated function with retry logic.

    This method was AI generated, and reviewed by a human.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_retries} attempts."
                        )
                        raise
                    else:
                        sleep_time = min(delay, max_delay)
                        sleep_time += jitter * (2 * random.random() - 1)  # Add jitter
                        logger.warning(
                            f"Attempt {attempt} for function '{func.__name__}' failed with {e.__class__.__name__}: {e} "
                            f"Retrying in {sleep_time:.2f} seconds..."
                        )
                        time.sleep(sleep_time)
                        delay *= backoff_factor

        return wrapper

    return decorator
