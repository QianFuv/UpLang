"""
Language file data model.
"""

from dataclasses import dataclass


@dataclass
class LanguageFile:
    """
    Represents a language file for a mod.
    """

    mod_id: str
    lang_code: str
    content: dict
    content_hash: str | None = None

    def __str__(self) -> str:
        key_count = len(self.content) if self.content else 0
        return f"{self.mod_id}/{self.lang_code}.json ({key_count} keys)"
