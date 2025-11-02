"""
Core functionality modules for UpLang.
"""

from uplang.core.scanner import ModScanner
from uplang.core.extractor import LanguageExtractor
from uplang.core.comparator import LanguageComparator
from uplang.core.cache import CacheManager
from uplang.core.synchronizer import LanguageSynchronizer

__all__ = [
    "ModScanner",
    "LanguageExtractor",
    "LanguageComparator",
    "CacheManager",
    "LanguageSynchronizer",
]
