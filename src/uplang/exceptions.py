"""
Custom exceptions for UpLang
"""


class UpLangError(Exception):
    """Base exception for UpLang"""
    pass


class ModScanError(UpLangError):
    """Error during mod scanning"""
    pass


class StateError(UpLangError):
    """Error with state management"""
    pass


class ExtractionError(UpLangError):
    """Error during language file extraction"""
    pass


class SynchronizationError(UpLangError):
    """Error during language file synchronization"""
    pass


class ConfigurationError(UpLangError):
    """Error with configuration"""
    pass


class FileSystemError(UpLangError):
    """Error with file system operations"""
    pass