"""
Language file extractor for extracting JSON files from JARs.
"""

from pathlib import Path
from zipfile import ZipFile

from uplang.exceptions import LanguageFileError
from uplang.models import LanguageFile, Mod
from uplang.utils import JSONHandler, calculate_dict_hash
from uplang.utils.output import print_verbose


class LanguageExtractor:
    """
    Extract language files from JAR files.
    """

    def __init__(self):
        self.json_handler = JSONHandler()

    def extract_language_files(
        self, mod: Mod, lang_codes: list[str] | None = None
    ) -> dict[str, LanguageFile]:
        """
        Extract language files from a mod JAR.
        """
        if lang_codes is None:
            lang_codes = ["en_us", "zh_cn"]

        result = {}

        try:
            with ZipFile(mod.jar_path, "r") as jar:
                for lang_code in lang_codes:
                    lang_file = self._extract_single_language(jar, mod, lang_code)
                    if lang_file:
                        result[lang_code] = lang_file

        except Exception as e:
            raise LanguageFileError(
                f"Failed to extract language files from {mod.jar_path}: {e}",
                context={"mod_id": mod.mod_id, "jar_path": str(mod.jar_path)},
            ) from e

        return result

    def _extract_single_language(
        self, jar: ZipFile, mod: Mod, lang_code: str
    ) -> LanguageFile | None:
        """
        Extract a single language file from JAR.
        """
        possible_paths = [
            f"assets/{mod.mod_id}/lang/{lang_code}.json",
            f"data/{mod.mod_id}/lang/{lang_code}.json",
        ]

        for path in possible_paths:
            try:
                if path in jar.namelist():
                    with jar.open(path) as f:
                        content = self.json_handler.load_from_bytes(f.read())

                    print_verbose(f"Extracted {mod.mod_id}/{lang_code}.json ({len(content)} keys)")

                    return LanguageFile(
                        mod_id=mod.mod_id,
                        lang_code=lang_code,
                        content=content,
                        content_hash=calculate_dict_hash(content),
                    )
            except Exception as e:
                print_verbose(
                    f"Failed to extract {path} from {mod.jar_path.name}: {e}"
                )
                continue

        return None

    def load_from_resource_pack(
        self, resourcepack_dir: Path, mod_id: str, lang_code: str
    ) -> LanguageFile | None:
        """
        Load a language file from the resource pack.
        """
        lang_file_path = (
            resourcepack_dir / "assets" / mod_id / "lang" / f"{lang_code}.json"
        )

        if not lang_file_path.exists():
            return None

        try:
            content = self.json_handler.load(lang_file_path)
            return LanguageFile(
                mod_id=mod_id,
                lang_code=lang_code,
                content=content,
                content_hash=calculate_dict_hash(content),
            )
        except Exception as e:
            raise LanguageFileError(
                f"Failed to load language file: {e}",
                context={"path": str(lang_file_path)},
            ) from e

    def save_to_resource_pack(
        self, resourcepack_dir: Path, lang_file: LanguageFile
    ) -> None:
        """
        Save a language file to the resource pack.
        """
        lang_file_path = (
            resourcepack_dir
            / "assets"
            / lang_file.mod_id
            / "lang"
            / f"{lang_file.lang_code}.json"
        )

        try:
            self.json_handler.dump(lang_file.content, lang_file_path)
            print_verbose(f"Saved {lang_file.mod_id}/{lang_file.lang_code}.json")
        except Exception as e:
            raise LanguageFileError(
                f"Failed to save language file: {e}",
                context={"path": str(lang_file_path)},
            ) from e
