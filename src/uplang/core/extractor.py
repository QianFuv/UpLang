"""
Language file extraction functionality
"""

import zipfile
from pathlib import Path
from typing import Optional, Tuple

from uplang.exceptions import ExtractionError
from uplang.logger import UpLangLogger
from uplang.models import Mod
from uplang.json_utils import read_json_robust


class LanguageExtractor:

    def __init__(self, logger: UpLangLogger):
        self.logger = logger

    def extract_language_file(self, mod: Mod, language: str) -> Optional[Tuple[str, bytes]]:
        """Extract a specific language file from a mod JAR"""
        try:
            with zipfile.ZipFile(mod.file_path, 'r') as jar_file:
                lang_file_path = self._find_language_file(jar_file, mod.mod_id, language)
                if not lang_file_path:
                    return None

                with jar_file.open(lang_file_path) as lang_file:
                    content = lang_file.read()

                    # Validate that the content is valid JSON before returning
                    if self._validate_json_content(content):
                        return lang_file_path, content
                    else:
                        self.logger.warning(f"Invalid JSON content in {lang_file_path} from {mod.mod_id}")
                        return None

        except (zipfile.BadZipFile, KeyError, OSError) as e:
            raise ExtractionError(f"Failed to extract {language} from {mod.mod_id}: {e}")

    def _find_language_file(self, jar_file: zipfile.ZipFile, mod_id: str, language: str) -> Optional[str]:
        """Find the language file path within the JAR"""
        filename = f"{language}.json"

        possible_paths = [
            f"assets/{mod_id}/lang/{filename}",
            f"data/{mod_id}/lang/{filename}",
        ]

        for path in possible_paths:
            if path in jar_file.namelist():
                return path

        for file_path in jar_file.namelist():
            if file_path.endswith(f"lang/{filename}") and mod_id in file_path:
                return file_path

        return None

    def extract_all_languages(self, mod: Mod) -> dict:
        """Extract all available language files from a mod"""
        languages = {}

        try:
            with zipfile.ZipFile(mod.file_path, 'r') as jar_file:
                for file_path in jar_file.namelist():
                    if '/lang/' in file_path and file_path.endswith('.json'):
                        lang_code = Path(file_path).stem

                        try:
                            with jar_file.open(file_path) as lang_file:
                                content = lang_file.read()

                                # Validate JSON content before including
                                if self._validate_json_content(content):
                                    languages[lang_code] = (file_path, content)
                                else:
                                    self.logger.debug(f"Skipped invalid JSON: {file_path} from {mod.mod_id}")
                        except Exception as e:
                            self.logger.warning(f"Failed to extract {file_path} from {mod.mod_id}: {e}")

        except (zipfile.BadZipFile, OSError) as e:
            raise ExtractionError(f"Failed to read JAR file {mod.file_path}: {e}")

        return languages

    def _validate_json_content(self, content_bytes: bytes) -> bool:
        """Validate that content is valid JSON"""
        try:
            # Try to decode and parse the content
            import tempfile
            import os

            # Create a temporary file to test JSON parsing
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
                temp_file.write(content_bytes)
                temp_path = Path(temp_file.name)

            try:
                # Use our robust JSON reader to validate
                data = read_json_robust(temp_path, self.logger)
                # Accept any valid dict, even empty ones like {}
                return isinstance(data, dict)
            finally:
                # Clean up temp file
                if temp_path.exists():
                    os.unlink(temp_path)

        except Exception:
            return False


def extract_lang_file(mod: Mod, lang_code: str = "en_us") -> Optional[Tuple[str, bytes]]:
    """Legacy function for backward compatibility"""
    from uplang.logger import get_logger
    extractor = LanguageExtractor(get_logger())
    return extractor.extract_language_file(mod, lang_code)