"""
Custom exception hierarchy for UpLang.
"""


class UpLangError(Exception):
    """
    Base exception for all UpLang errors.
    """

    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class ModNotFoundError(UpLangError):
    """
    Raised when a mod JAR file cannot be found or accessed.
    """

    pass


class ModMetadataError(UpLangError):
    """
    Raised when mod metadata cannot be extracted or is invalid.
    """

    pass


class LanguageFileError(UpLangError):
    """
    Raised when a language file cannot be read, parsed, or written.
    """

    pass


class JSONParseError(LanguageFileError):
    """
    Raised when JSON parsing fails.
    """

    pass


class SyncError(UpLangError):
    """
    Raised when synchronization fails.
    """

    pass


class CacheError(UpLangError):
    """
    Raised when cache operations fail.
    """

    pass


class ValidationError(UpLangError):
    """
    Raised when input validation fails.
    """

    pass
