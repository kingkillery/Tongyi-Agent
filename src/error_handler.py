"""
Centralized Error Handling Module
---------------------------------
Provides user-friendly error messages, retry utilities with exponential backoff,
and graceful fallback mechanisms for the Tongyi Agent.

Key Features:
- Custom exception classes for different error types
- User-friendly error message generators with actionable guidance
- Retry utilities with exponential backoff and jitter
- Graceful fallback helpers for API failures
"""
from __future__ import annotations

import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Type, TypeVar

import requests


# ============================================================================
# Custom Exception Classes
# ============================================================================

class TongyiAgentError(Exception):
    """Base exception for all Tongyi Agent errors."""
    pass


class ConfigurationError(TongyiAgentError):
    """Raised when configuration is invalid or missing."""
    pass


class APIKeyError(TongyiAgentError):
    """Raised when API key is invalid or missing."""
    pass


class NetworkError(TongyiAgentError):
    """Raised when network operations fail."""
    pass


class RateLimitError(TongyiAgentError):
    """Raised when API rate limits are exceeded."""
    pass


class ModelNotFoundError(TongyiAgentError):
    """Raised when requested model is not available."""
    pass


class ValidationError(TongyiAgentError):
    """Raised when user input validation fails."""
    pass


class TimeoutError(TongyiAgentError):
    """Raised when operations timeout."""
    pass


# ============================================================================
# Error Message Generators
# ============================================================================

def get_api_unavailable_message(error: Optional[Exception] = None) -> str:
    """
    Generate user-friendly message for API unavailability.

    Args:
        error: The underlying exception (optional)

    Returns:
        User-friendly error message with troubleshooting steps
    """
    header = "The OpenRouter service is currently unavailable."
    reason = f"\nCause: {error}" if error else ""

    steps = [
        "Check your internet connection",
        "Verify OPENROUTER_API_KEY is set in your .env file",
        "Run 'python -m config_validator --check-openrouter' for diagnostics",
        "Try again in a few minutes",
    ]

    steps_text = "\n".join(f"  • {step}" for step in steps)
    return f"{header}{reason}\n\nTroubleshooting steps:\n{steps_text}"


def get_invalid_api_key_message(error: Optional[Exception] = None) -> str:
    """
    Generate user-friendly message for invalid API key.

    Args:
        error: The underlying exception (optional)

    Returns:
        User-friendly error message with troubleshooting steps
    """
    header = "Your OpenRouter API key appears invalid or missing."
    reason = f"\nCause: {error}" if error else ""

    steps = [
        "Open your .env file in the project root",
        "Add or update: OPENROUTER_API_KEY=your_actual_api_key_here",
        "Get a valid API key from https://openrouter.ai/keys",
        "Run 'python -m config_validator --check-openrouter' to verify",
    ]

    steps_text = "\n".join(f"  • {step}" for step in steps)
    return f"{header}{reason}\n\nTroubleshooting steps:\n{steps_text}"


def get_model_unavailable_message(model_name: str, error: Optional[Exception] = None) -> str:
    """
    Generate user-friendly message for unavailable model.

    Args:
        model_name: Name of the unavailable model
        error: The underlying exception (optional)

    Returns:
        User-friendly error message with suggestions
    """
    header = f"The requested model '{model_name}' is not available or cannot be accessed."
    reason = f"\nCause: {error}" if error else ""

    steps = [
        f"Verify the model name is correct: '{model_name}'",
        "Run 'python -m config_validator --check-openrouter' to see available models",
        "Try a different model using 'tongyi-cli models set <model>'",
        "Check models.ini for fallback model configuration",
    ]

    steps_text = "\n".join(f"  • {step}" for step in steps)
    return f"{header}{reason}\n\nTroubleshooting steps:\n{steps_text}"


def get_rate_limit_message(error: Optional[Exception] = None) -> str:
    """
    Generate user-friendly message for rate limit exceeded.

    Args:
        error: The underlying exception (optional)

    Returns:
        User-friendly error message with suggestions
    """
    header = "API rate limit exceeded. Too many requests in a short period."
    reason = f"\nCause: {error}" if error else ""

    steps = [
        "Wait a minute before retrying",
        "Reduce the frequency of API calls",
        "Use a fallback model configured in models.ini",
        "Consider upgrading your OpenRouter plan for higher limits",
    ]

    steps_text = "\n".join(f"  • {step}" for step in steps)
    return f"{header}{reason}\n\nTroubleshooting steps:\n{steps_text}"


def get_network_error_message(error: Optional[Exception] = None) -> str:
    """
    Generate user-friendly message for network errors.

    Args:
        error: The underlying exception (optional)

    Returns:
        User-friendly error message with troubleshooting steps
    """
    header = "Network error occurred while connecting to the API."
    reason = f"\nCause: {error}" if error else ""

    steps = [
        "Check your internet connection",
        "Verify your proxy settings if applicable",
        "Try disabling VPN or firewall temporarily",
        "Run 'python -m config_validator --check-openrouter' to test connectivity",
    ]

    steps_text = "\n".join(f"  • {step}" for step in steps)
    return f"{header}{reason}\n\nTroubleshooting steps:\n{steps_text}"


def get_timeout_message(timeout_seconds: int, error: Optional[Exception] = None) -> str:
    """
    Generate user-friendly message for operation timeouts.

    Args:
        timeout_seconds: The timeout duration in seconds
        error: The underlying exception (optional)

    Returns:
        User-friendly error message with suggestions
    """
    header = f"Operation timed out after {timeout_seconds} seconds."
    reason = f"\nCause: {error}" if error else ""

    steps = [
        "Your question may be too complex - try breaking it into smaller parts",
        "The network may be slow - check your connection",
        "Try again in a few minutes when the service is less busy",
    ]

    steps_text = "\n".join(f"  • {step}" for step in steps)
    return f"{header}{reason}\n\nTroubleshooting steps:\n{steps_text}"


def get_invalid_input_message(field_name: str, value: Any, expected: str) -> str:
    """
    Generate user-friendly message for invalid input validation.

    Args:
        field_name: Name of the field that failed validation
        value: The invalid value
        expected: Description of what was expected

    Returns:
        User-friendly error message
    """
    return (
        f"Invalid {field_name}: '{value}'.\n\n"
        f"Expected: {expected}\n\n"
        f"Please correct your input and try again."
    )


def get_invalid_path_message(path: str, reason: str = "does not exist") -> str:
    """
    Generate user-friendly message for invalid file/directory paths.

    Args:
        path: The invalid path
        reason: Reason why the path is invalid

    Returns:
        User-friendly error message with suggestions
    """
    header = f"The path '{path}' {reason}."
    steps = [
        "Verify the path is correct",
        "Check that the file/directory exists",
        "Use absolute paths if relative paths are not working",
        "On Windows, use forward slashes (/) or escaped backslashes (\\\\)",
    ]

    steps_text = "\n".join(f"  • {step}" for step in steps)
    return f"{header}\n\nTroubleshooting steps:\n{steps_text}"


def get_fallback_enabled_message(primary_model: str, fallback_model: str) -> str:
    """
    Generate message when fallback mode is activated.

    Args:
        primary_model: The primary model that failed
        fallback_model: The fallback model being used

    Returns:
        User-friendly informational message
    """
    return (
        f"Primary model '{primary_model}' is unavailable. "
        f"Falling back to '{fallback_model}'.\n\n"
        f"Note: Run 'python -m config_validator --check-openrouter' to diagnose the issue."
    )


# ============================================================================
# Retry Utilities with Exponential Backoff and Jitter
# ============================================================================

T = TypeVar("T")


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """
    Calculate backoff delay with exponential increase and optional jitter.

    Args:
        attempt: Current retry attempt (1-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter to avoid thundering herd

    Returns:
        Delay in seconds

    Examples:
        >>> calculate_backoff(1, base_delay=1.0)
        1.0
        >>> calculate_backoff(2, base_delay=1.0)
        2.0
        >>> calculate_backoff(3, base_delay=1.0)
        4.0
    """
    # Calculate exponential backoff
    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)

    # Add random jitter to distribute retry attempts
    if jitter:
        delay *= random.uniform(0.8, 1.2)

    return delay


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.

    Args:
        error: The exception to check

    Returns:
        True if error should trigger a retry, False otherwise
    """
    # Network-related errors
    if isinstance(error, (requests.ConnectionError, requests.Timeout)):
        return True

    # HTTP errors that might be transient
    if isinstance(error, requests.HTTPError):
        status_code = error.response.status_code if hasattr(error, 'response') else None
        if status_code:
            # Retry on rate limits, server errors, and timeouts
            return status_code in {408, 429, 500, 502, 503, 504}

    # Custom retryable errors
    if isinstance(error, (NetworkError, RateLimitError, TimeoutError)):
        return True

    return False


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    fallback_result: Optional[T] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying functions on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        retryable_exceptions: Tuple of exception types to catch and retry
        fallback_result: Value to return if all retries fail
        on_retry: Callback function called before each retry (attempt, error)

    Returns:
        Decorated function with retry logic

    Examples:
        >>> @retry_on_failure(max_retries=3)
        >>> def fetch_data(url):
        ...     return requests.get(url)

        >>> @retry_on_failure(max_retries=2, fallback_result=None)
        >>> def risky_operation():
        ...     return some_api_call()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    # Check if this error is retryable
                    is_retryable = is_retryable_error(e)
                    if retryable_exceptions and isinstance(e, retryable_exceptions):
                        is_retryable = True

                    # If not retryable or out of retries, handle the error
                    if not is_retryable or attempt == max_retries:
                        if fallback_result is not None:
                            return fallback_result
                        raise

                    # Calculate delay and sleep before retry
                    delay = calculate_backoff(
                        attempt=attempt + 1,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        exponential_base=exponential_base,
                        jitter=jitter
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e)

                    time.sleep(delay)

            # This should never be reached, but for type safety
            if fallback_result is not None:
                return fallback_result
            raise last_error

        return wrapper
    return decorator


# ============================================================================
# Graceful Fallback Helpers
# ============================================================================

class FallbackHandler:
    """
    Helper class for managing graceful fallbacks between alternatives.

    Examples:
        >>> handler = FallbackHandler(
        ...     primary=lambda: call_api_primary(),
        ...     fallback=lambda: call_api_fallback(),
        ...     on_fallback=lambda err: print(f"Using fallback: {err}")
        ... )
        >>> result = handler.execute()
    """

    def __init__(
        self,
        primary: Callable[[], T],
        fallback: Callable[[], T],
        on_fallback: Optional[Callable[[Exception], None]] = None,
        fallback_error_type: Type[Exception] = Exception,
    ):
        """
        Initialize the fallback handler.

        Args:
            primary: Primary operation function
            fallback: Fallback operation function
            on_fallback: Callback when fallback is activated
            fallback_error_type: Exception type that triggers fallback
        """
        self.primary = primary
        self.fallback = fallback
        self.on_fallback = on_fallback
        self.fallback_error_type = fallback_error_type

    def execute(self) -> T:
        """
        Execute primary operation, falling back to alternative on failure.

        Returns:
            Result from primary or fallback operation

        Raises:
            FallbackError: If both primary and fallback fail
        """
        try:
            return self.primary()
        except Exception as e:
            # Trigger fallback on specific error types
            if isinstance(e, self.fallback_error_type):
                if self.on_fallback:
                    self.on_fallback(e)

                try:
                    return self.fallback()
                except Exception as fallback_error:
                    raise TongyiAgentError(
                        f"Both primary and fallback operations failed. "
                        f"Primary error: {e}. Fallback error: {fallback_error}"
                    ) from fallback_error
            else:
                # Re-raise non-fallback errors
                raise


def with_fallback(
    fallback_func: Callable[[], T],
    fallback_error_type: Type[Exception] = Exception,
    on_fallback: Optional[Callable[[Exception], None]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for adding fallback logic to functions.

    Args:
        fallback_func: Fallback function to call on error
        fallback_error_type: Exception type that triggers fallback
        on_fallback: Callback when fallback is activated

    Returns:
        Decorated function with fallback logic

    Examples:
        >>> @with_fallback(lambda: local_search(query))
        >>> def web_search(query):
        ...     return external_api.search(query)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, fallback_error_type):
                    if on_fallback:
                        on_fallback(e)
                    return fallback_func()
                raise
        return wrapper
    return decorator


# ============================================================================
# Input Validation Helpers
# ============================================================================

def validate_api_key(api_key: str, key_name: str = "API key") -> str:
    """
    Validate an API key format.

    Args:
        api_key: The API key to validate
        key_name: Name of the key for error messages

    Returns:
        The validated API key

    Raises:
        ValidationError: If the API key is invalid
    """
    if not api_key:
        raise ValidationError(
            get_invalid_input_message(key_name, api_key, "a non-empty string")
        )

    if len(api_key) < 10:
        raise ValidationError(
            get_invalid_input_message(
                key_name, api_key[:4] + "...", "at least 10 characters long"
            )
        )

    return api_key


def validate_file_path(path: str, must_exist: bool = True) -> str:
    """
    Validate a file path.

    Args:
        path: The file path to validate
        must_exist: Whether the file must exist

    Returns:
        The validated absolute path

    Raises:
        ValidationError: If the path is invalid
    """
    from pathlib import Path

    p = Path(path).expanduser().absolute()

    if must_exist and not p.exists():
        raise ValidationError(
            get_invalid_path_message(str(p), "does not exist")
        )

    if must_exist and not p.is_file():
        raise ValidationError(
            get_invalid_path_message(str(p), "is not a file")
        )

    return str(p)


def validate_directory_path(path: str, must_exist: bool = True) -> str:
    """
    Validate a directory path.

    Args:
        path: The directory path to validate
        must_exist: Whether the directory must exist

    Returns:
        The validated absolute path

    Raises:
        ValidationError: If the path is invalid
    """
    from pathlib import Path

    p = Path(path).expanduser().absolute()

    if must_exist and not p.exists():
        raise ValidationError(
            get_invalid_path_message(str(p), "does not exist")
        )

    if must_exist and not p.is_dir():
        raise ValidationError(
            get_invalid_path_message(str(p), "is not a directory")
        )

    return str(p)


def validate_question(question: str, min_length: int = 5) -> str:
    """
    Validate a user question.

    Args:
        question: The question to validate
        min_length: Minimum length requirement

    Returns:
        The validated question

    Raises:
        ValidationError: If the question is invalid
    """
    if not question:
        raise ValidationError(
            get_invalid_input_message("question", question, "a non-empty string")
        )

    if len(question.strip()) < min_length:
        raise ValidationError(
            get_invalid_input_message(
                "question",
                question.strip(),
                f"at least {min_length} characters long"
            )
        )

    return question.strip()


def validate_model_name(model_name: str, available_models: set[str]) -> str:
    """
    Validate a model name against available models.

    Args:
        model_name: The model name to validate
        available_models: Set of available model names

    Returns:
        The validated model name

    Raises:
        ValidationError: If the model is not available
    """
    if not model_name:
        raise ValidationError(
            get_invalid_input_message("model", model_name, "a non-empty string")
        )

    if model_name not in available_models:
        available_sample = ", ".join(list(available_models)[:3])
        raise ValidationError(
            get_invalid_input_message(
                "model",
                model_name,
                f"one of the available models (e.g., {available_sample}, ...)"
            )
        )

    return model_name


# ============================================================================
# Error Formatting Utilities
# ============================================================================

def format_error_for_user(
    error: Exception,
    include_traceback: bool = False,
    context: Optional[str] = None
) -> str:
    """
    Format an exception for user-friendly display.

    Args:
        error: The exception to format
        include_traceback: Whether to include traceback
        context: Optional context information

    Returns:
        Formatted error message
    """
    parts = []

    # Add context if provided
    if context:
        parts.append(f"Context: {context}")

    # Add error type and message
    error_type = type(error).__name__
    error_msg = str(error)
    parts.append(f"Error ({error_type}): {error_msg}")

    # Add suggestions for known error types
    if isinstance(error, (APIKeyError, ConfigurationError)):
        parts.append(get_invalid_api_key_message(error))
    elif isinstance(error, RateLimitError):
        parts.append(get_rate_limit_message(error))
    elif isinstance(error, ModelNotFoundError):
        parts.append(get_model_unavailable_message("requested model", error))
    elif isinstance(error, (NetworkError, requests.ConnectionError, requests.Timeout)):
        parts.append(get_network_error_message(error))
    elif isinstance(error, ValidationError):
        # ValidationError already contains a formatted message
        parts.append(error_msg)

    # Add traceback if requested
    if include_traceback:
        import traceback
        parts.append(f"\nTraceback:\n{traceback.format_exc()}")

    return "\n\n".join(parts)
