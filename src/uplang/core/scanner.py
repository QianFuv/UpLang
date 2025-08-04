"""
Scanner module for extracting language files from Minecraft mod JAR files.

This module provides functionality to scan directories for Minecraft mod JAR files,
extract mod IDs from META-INF/mods.toml using tomllib, and optionally extract en_us.json 
and zh_cn.json language files using the standard json library. All mods are recorded 
regardless of whether they have language files.
"""

import os
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass
import logging
import tomllib

import json

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LanguageFile:
    """
    Represents a single language file extracted from a Minecraft mod.
    
    Attributes:
        language_code: Language code ('en_us' or 'zh_cn')
        file_path: Path within the JAR file
        translations: Dictionary of translation keys and values
    """
    language_code: str
    file_path: str
    translations: Dict[str, str]


@dataclass(frozen=True)
class ModLanguageData:
    """
    Contains language data for a single mod.
    
    Attributes:
        mod_id: The identifier of the mod
        jar_path: Path to the JAR file
        en_us: English language file if present
        zh_cn: Chinese language file if present
    """
    mod_id: str
    jar_path: str
    en_us: Optional[LanguageFile] = None
    zh_cn: Optional[LanguageFile] = None


@dataclass(frozen=True)
class ScanResult:
    """
    Results of scanning a directory for mod language files.
    
    Attributes:
        scanned_directory: Path that was scanned
        total_jars: Total number of JAR files found
        processed_jars: Number of JAR files successfully processed (mod ID extracted)
        mod_languages: Dictionary mapping mod IDs to their language data
        errors: List of error messages encountered during scanning
    """
    scanned_directory: str
    total_jars: int
    processed_jars: int
    mod_languages: Dict[str, ModLanguageData]
    errors: List[str]


class LanguageFileExtractor:
    """
    Handles extraction and parsing of language files from JAR archives.
    """
    
    LANGUAGE_PATH_PREFIX = "assets/"
    LANGUAGE_PATH_SUFFIX = "/lang/"
    MODS_TOML_PATH = "META-INF/mods.toml"
    SUPPORTED_LANGUAGES = {"en_us", "zh_cn"}
    
    def extract_from_jar(self, jar_path: Path) -> Optional[ModLanguageData]:
        """
        Extract mod data from a single JAR file, including mod ID and language files.
        
        Args:
            jar_path: Path to the JAR file
            
        Returns:
            ModLanguageData object with mod ID from mods.toml, None if mod ID cannot be extracted
        """
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar_file:
                mod_id = self._extract_mod_id_from_toml(jar_file)
                
                if not mod_id:
                    logger.warning(f"No mod ID found in {jar_path}")
                    return None
                
                language_files = self._find_supported_language_files(jar_file, mod_id)
                
                en_us_file = None
                zh_cn_file = None
                
                for file_path in language_files:
                    lang_file = self._parse_language_file(jar_file, file_path)
                    if lang_file:
                        if lang_file.language_code == "en_us":
                            en_us_file = lang_file
                        elif lang_file.language_code == "zh_cn":
                            zh_cn_file = lang_file
                
                return ModLanguageData(
                    mod_id=mod_id,
                    jar_path=str(jar_path),
                    en_us=en_us_file,
                    zh_cn=zh_cn_file
                )
                
        except (zipfile.BadZipFile, PermissionError, OSError) as e:
            logger.warning(f"Failed to process JAR file {jar_path}: {e}")
        
        return None
    
    def _extract_mod_id_from_toml(self, jar_file: zipfile.ZipFile) -> Optional[str]:
        """
        Extract mod ID from META-INF/mods.toml file.
        
        Args:
            jar_file: Opened ZipFile object
            
        Returns:
            Mod ID if found, None otherwise
        """
        try:
            with jar_file.open(self.MODS_TOML_PATH) as toml_file:
                content = toml_file.read()
                toml_data = tomllib.loads(content.decode('utf-8'))
                
                # Look for modId in the mods array (typical structure)
                if 'mods' in toml_data and isinstance(toml_data['mods'], list):
                    for mod in toml_data['mods']:
                        if isinstance(mod, dict) and 'modId' in mod:
                            return mod['modId']
                
                # Fallback: look for modId at root level
                if 'modId' in toml_data:
                    return toml_data['modId']
                
        except (KeyError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            logger.debug(f"Failed to read mods.toml: {e}")
        
        return None
    
    def _find_supported_language_files(self, jar_file: zipfile.ZipFile, mod_id: str) -> List[str]:
        """
        Find en_us.json and zh_cn.json language files for a specific mod within the JAR archive.
        
        Args:
            jar_file: Opened ZipFile object
            mod_id: The mod ID to look for
            
        Returns:
            List of file paths for supported language files
        """
        language_files = []
        expected_path_prefix = f"{self.LANGUAGE_PATH_PREFIX}{mod_id}{self.LANGUAGE_PATH_SUFFIX}"
        
        for file_path in jar_file.namelist():
            if file_path.startswith(expected_path_prefix):
                filename = file_path.split('/')[-1]
                if filename.replace('.json', '') in self.SUPPORTED_LANGUAGES:
                    language_files.append(file_path)
        
        return language_files
    
    def _parse_language_file(self, jar_file: zipfile.ZipFile, file_path: str) -> Optional[LanguageFile]:
        """
        Parse a single language file from the JAR archive.
        
        Args:
            jar_file: Opened ZipFile object
            file_path: Path to the language file within the JAR
            
        Returns:
            LanguageFile object if successful, None otherwise
        """
        try:
            with jar_file.open(file_path) as lang_file:
                content = lang_file.read()
                translations = json.loads(content.decode('utf-8'))
                
                if not isinstance(translations, dict):
                    logger.warning(f"Invalid language file format in {file_path}")
                    return None
                
                # Convert all values to strings to ensure consistency
                string_translations = {
                    key: str(value) for key, value in translations.items()
                    if isinstance(key, str)
                }
                
                language_code = self._extract_language_code_from_path(file_path)
                
                return LanguageFile(
                    language_code=language_code,
                    file_path=file_path,
                    translations=string_translations
                )
                
        except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse language file {file_path}: {e}")
        
        return None
    
    def _extract_language_code_from_path(self, file_path: str) -> str:
        """
        Extract language code from the file path.
        
        Args:
            file_path: Path to the language file (e.g., 'assets/modid/lang/en_us.json')
            
        Returns:
            The language code (en_us or zh_cn)
        """
        filename = file_path.split('/')[-1]
        language_code = filename.replace('.json', '')
        
        if language_code not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language code: {language_code}")
        
        return language_code


class DirectoryScanner:
    """
    Handles scanning directories for JAR files.
    """
    
    JAR_EXTENSION = ".jar"
    
    def scan_for_jars(self, directory: Path, recursive: bool = True) -> Iterator[Path]:
        """
        Scan directory for JAR files.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories recursively
            
        Yields:
            Path objects for found JAR files
        """
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory does not exist or is not a directory: {directory}")
            return
        
        pattern = "**/*" if recursive else "*"
        
        for path in directory.glob(pattern):
            if path.is_file() and path.suffix.lower() == self.JAR_EXTENSION:
                yield path


class Scanner:
    """
    Main scanner class for extracting mod data and language files from Minecraft mod directories.
    
    Records all mods found in JAR files based on their mod IDs from META-INF/mods.toml,
    and optionally extracts en_us and zh_cn language files when available.
    """
    
    def __init__(self):
        """Initialize the scanner with default components."""
        self.extractor = LanguageFileExtractor()
        self.directory_scanner = DirectoryScanner()
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> ScanResult:
        """
        Scan a directory for Minecraft mod JAR files and extract language data.
        
        Args:
            directory_path: Path to the directory containing mod JAR files
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            ScanResult containing all mod data indexed by mod ID
        """
        directory = Path(directory_path)
        mod_languages = {}
        errors = []
        total_jars = 0
        processed_jars = 0
        
        logger.info(f"Starting scan of directory: {directory}")
        
        for jar_path in self.directory_scanner.scan_for_jars(directory, recursive):
            total_jars += 1
            
            try:
                mod_data = self.extractor.extract_from_jar(jar_path)
                
                if mod_data:
                    if mod_data.mod_id in mod_languages:
                        error_msg = f"Duplicate mod ID '{mod_data.mod_id}' found in {jar_path}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                    else:
                        mod_languages[mod_data.mod_id] = mod_data
                        processed_jars += 1
                        
                        languages_found = []
                        if mod_data.en_us:
                            languages_found.append("en_us")
                        if mod_data.zh_cn:
                            languages_found.append("zh_cn")
                        
                        if languages_found:
                            logger.debug(f"Processed mod: {mod_data.mod_id} with languages: {languages_found}")
                        else:
                            logger.debug(f"Processed mod: {mod_data.mod_id} with no language files")
                else:
                    logger.debug(f"Skipped {jar_path}: no mod ID found")
                
            except Exception as e:
                error_msg = f"Unexpected error processing {jar_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Scan completed: {processed_jars}/{total_jars} JAR files processed successfully")
        
        return ScanResult(
            scanned_directory=str(directory),
            total_jars=total_jars,
            processed_jars=processed_jars,
            mod_languages=mod_languages,
            errors=errors
        )
    
    def get_mods_with_english(self, scan_result: ScanResult) -> List[str]:
        """
        Get list of mod IDs that have English translations.
        
        Args:
            scan_result: Result from a directory scan
            
        Returns:
            List of mod IDs that have en_us.json files
        """
        return [
            mod_id for mod_id, mod_data in scan_result.mod_languages.items()
            if mod_data.en_us is not None
        ]
    
    def get_mods_with_chinese(self, scan_result: ScanResult) -> List[str]:
        """
        Get list of mod IDs that have Chinese translations.
        
        Args:
            scan_result: Result from a directory scan
            
        Returns:
            List of mod IDs that have zh_cn.json files
        """
        return [
            mod_id for mod_id, mod_data in scan_result.mod_languages.items()
            if mod_data.zh_cn is not None
        ]
    
    def get_mods_with_both_languages(self, scan_result: ScanResult) -> List[str]:
        """
        Get list of mod IDs that have both English and Chinese translations.
        
        Args:
            scan_result: Result from a directory scan
            
        Returns:
            List of mod IDs that have both en_us.json and zh_cn.json files
        """
        return [
            mod_id for mod_id, mod_data in scan_result.mod_languages.items()
            if mod_data.en_us is not None and mod_data.zh_cn is not None
        ]
    
    def get_mods_without_languages(self, scan_result: ScanResult) -> List[str]:
        """
        Get list of mod IDs that have no language files.
        
        Args:
            scan_result: Result from a directory scan
            
        Returns:
            List of mod IDs that have neither en_us.json nor zh_cn.json files
        """
        return [
            mod_id for mod_id, mod_data in scan_result.mod_languages.items()
            if mod_data.en_us is None and mod_data.zh_cn is None
        ]