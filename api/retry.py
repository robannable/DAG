"""Retry logic with exponential backoff for API requests"""
import time
import logging
from typing import Callable, Any, Optional
import requests


class RetryConfig:
    """Configuration for retry logic"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base


def retry_with_exponential_backoff(
    func: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff

    Args:
        func: The function to retry
        config: Retry configuration (uses defaults if None)
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        The result of the successful function call

    Raises:
        The last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return func(*args, **kwargs)
        except (
            requests.exceptions.RequestException,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ) as e:
            last_exception = e

            if attempt < config.max_retries:
                # Calculate delay with exponential backoff
                delay = min(
                    config.base_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )

                logging.warning(
                    f"Attempt {attempt + 1}/{config.max_retries + 1} failed: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )

                time.sleep(delay)
            else:
                logging.error(
                    f"All {config.max_retries + 1} attempts failed. Last error: {str(e)}"
                )

    # If we get here, all retries failed
    raise last_exception


def make_api_request_with_retry(
    url: str,
    headers: dict,
    data: dict,
    config: Optional[RetryConfig] = None,
    timeout: int = 60
) -> requests.Response:
    """
    Make an API POST request with retry logic

    Args:
        url: The API endpoint URL
        headers: Request headers
        data: Request payload
        config: Retry configuration
        timeout: Request timeout in seconds

    Returns:
        Response object

    Raises:
        requests.exceptions.RequestException: If all retries fail
    """

    def _make_request():
        response = requests.post(url, headers=headers, json=data, timeout=timeout)
        # Only retry on specific status codes (server errors, rate limits)
        if response.status_code in [429, 500, 502, 503, 504]:
            logging.warning(f"Received status code {response.status_code}, will retry")
            raise requests.exceptions.RequestException(
                f"Server returned {response.status_code}"
            )
        return response

    return retry_with_exponential_backoff(_make_request, config)
