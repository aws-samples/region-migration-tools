"""
Utility functions for handling AWS Bedrock throttling and rate limiting.
"""

import time
import random
import logging
from typing import Callable, Any
from functools import wraps
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def with_throttling_retry(max_retries: int = 3, base_delay: float = 2.0):
    """
    Decorator to add throttling retry logic to functions that call Bedrock.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if is_throttling_error(e) and attempt < max_retries:
                        delay = calculate_backoff_delay(attempt, base_delay)
                        logger.warning(
                            f"Throttling detected in {func.__name__}, "
                            f"retrying in {delay:.2f} seconds "
                            f"(attempt {attempt + 1}/{max_retries + 1})"
                        )
                        time.sleep(delay)
                    else:
                        raise e
            return None  # Should never reach here
        return wrapper
    return decorator


def is_throttling_error(error: Exception) -> bool:
    """
    Check if an error is a throttling-related error.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is throttling-related, False otherwise
    """
    error_str = str(error).lower()
    throttling_indicators = [
        'throttlingexception',
        'too many requests',
        'rate exceeded',
        'throttled',
        'request limit exceeded'
    ]
    
    return any(indicator in error_str for indicator in throttling_indicators)


def calculate_backoff_delay(attempt: int, base_delay: float) -> float:
    """
    Calculate exponential backoff delay with jitter.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        
    Returns:
        Delay in seconds with jitter applied
    """
    # Exponential backoff: base_delay * (2 ^ attempt)
    exponential_delay = base_delay * (2 ** attempt)
    
    # Add jitter to avoid thundering herd problem
    jitter = random.uniform(0, exponential_delay * 0.1)
    
    return exponential_delay + jitter


def rate_limited_call(func: Callable, delay: float = 1.0) -> Any:
    """
    Execute a function with rate limiting.
    
    Args:
        func: Function to execute
        delay: Delay in seconds before executing
        
    Returns:
        Result of the function call
    """
    time.sleep(delay)
    return func()


class ThrottlingHandler:
    """
    Context manager for handling throttling in batch operations.
    """
    
    def __init__(self, delay_between_calls: float = 1.0, max_retries: int = 3):
        self.delay_between_calls = delay_between_calls
        self.max_retries = max_retries
        self.call_count = 0
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def execute_with_throttling(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with throttling protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
        """
        # Add delay between calls
        if self.call_count > 0:
            time.sleep(self.delay_between_calls)
            
        # Execute with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self.call_count += 1
                return result
            except Exception as e:
                if is_throttling_error(e) and attempt < self.max_retries:
                    delay = calculate_backoff_delay(attempt, 2.0)
                    logger.warning(
                        f"Throttling detected, retrying in {delay:.2f} seconds "
                        f"(attempt {attempt + 1}/{self.max_retries + 1})"
                    )
                    time.sleep(delay)
                else:
                    raise e
        
        return None  # Should never reach here