"""
Custom exceptions for UpLang with enhanced error handling.

This module defines a hierarchy of exceptions used throughout UpLang,
with support for context information and error recovery strategies.
"""

from typing import Optional, Dict, Any
from functools import wraps
import traceback


class UpLangError(Exception):
    """Base exception for UpLang with context support.

    All UpLang-specific exceptions inherit from this class.
    Provides support for context information and chained exceptions.
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        """Initialize exception with message, context, and optional cause."""
        super().__init__(message)
        self.context = context or {}
        self.cause = cause
        self.traceback_str = traceback.format_exc() if cause else None

    def __str__(self):
        """Return string representation including context."""
        base_msg = super().__str__()
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg += f" (Context: {context_str})"
        return base_msg


class ModScanError(UpLangError):
    """Error during mod scanning operations."""
    pass


class StateError(UpLangError):
    """Error with state management operations."""
    pass


class ExtractionError(UpLangError):
    """Error during language file extraction from JAR files."""
    pass


class SynchronizationError(UpLangError):
    """Error during language file synchronization operations."""
    pass


class ConfigurationError(UpLangError):
    """Error with configuration validation or loading."""
    pass


class FileSystemError(UpLangError):
    """Error with file system operations."""
    pass


class ValidationError(UpLangError):
    """Error with data validation operations."""
    pass


def handle_errors(error_type: type[Exception] = UpLangError, default_return=None, log_error: bool = True):
    """Decorator for unified error handling.

    Args:
        error_type: Expected exception type to handle
        default_return: Default value to return on error
        log_error: Whether to log unexpected errors
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_type:
                # Re-raise expected errors
                raise
            except Exception as e:
                # Convert unexpected errors to expected type
                context = {
                    'function': func.__name__,
                    'args_count': len(args),
                    'kwargs': list(kwargs.keys())
                }

                # Try to get logger from args if available
                logger = None
                for arg in args:
                    if hasattr(arg, 'logger'):
                        logger = arg.logger
                        break

                if log_error and logger:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")

                if default_return is not None:
                    return default_return

                if issubclass(error_type, UpLangError):
                    raise error_type(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        context=context,
                        cause=e
                    )
                else:
                    raise error_type(f"Unexpected error in {func.__name__}: {str(e)}")
        return wrapper
    return decorator


class ErrorRecovery:
    """Utility class for error recovery strategies."""

    @staticmethod
    def retry_on_failure(func, max_retries: int = 3, exceptions: tuple = (Exception,)):
        """Retry function on failure up to max_retries times.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            exceptions: Tuple of exceptions to catch and retry on
        """
        for attempt in range(max_retries):
            try:
                return func()
            except exceptions as e:
                if attempt == max_retries - 1:
                    raise e
                continue

    @staticmethod
    def safe_execute(func, default_return=None, logger=None):
        """Execute function safely with fallback.

        Args:
            func: Function to execute
            default_return: Value to return on error
            logger: Optional logger for warning messages
        """
        try:
            return func()
        except Exception as e:
            if logger:
                logger.warning(f"Safe execution failed: {e}")
            return default_return