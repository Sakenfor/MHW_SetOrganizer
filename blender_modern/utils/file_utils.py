"""
File and path utilities for MHW Set Organizer.

Handles file I/O, path construction, and settings management.
"""

import os
import json
from typing import Dict, Optional, Any
from pathlib import Path

import bpy

from .. import addon_config


def get_addon_directory() -> Path:
    """
    Get the base directory of the addon.

    Returns:
        Path object pointing to the addon directory.
    """
    return Path(__file__).parent.parent


def get_settings_path() -> Path:
    """
    Get the path to the settings JSON file.

    Returns:
        Path object pointing to MhwSettings.json
    """
    return get_addon_directory() / addon_config.SETTINGS_FILENAME


def load_settings() -> Dict[str, Any]:
    """
    Load addon settings from JSON file.

    Returns:
        Dictionary containing settings, or empty dict if file doesn't exist.

    Raises:
        json.JSONDecodeError: If settings file is corrupted.
    """
    settings_path = get_settings_path()

    if not settings_path.exists():
        return {}

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error loading settings from {settings_path}: {e}")
        return {}


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save addon settings to JSON file.

    Args:
        settings: Dictionary containing settings to save.

    Returns:
        True if successful, False otherwise.
    """
    settings_path = get_settings_path()

    try:
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, sort_keys=True)
        return True
    except (OSError, TypeError) as e:
        print(f"Error saving settings to {settings_path}: {e}")
        return False


def load_armor_database() -> Dict[str, str]:
    """
    Load the clothes_num.json armor database.

    Returns:
        Dictionary mapping armor IDs to names.

    Example:
        {'pl001_0000': 'Leather', 'pl002_0000': 'Chain'}
    """
    data_path = get_addon_directory() / 'data' / 'clothes_num.json'

    if not data_path.exists():
        print(f"Warning: Armor database not found at {data_path}")
        return {}

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Parse the format "pl001_0000__ArmorName": "ArmorName"
        parsed = {}
        for key, value in data.items():
            if '__' in key:
                armor_id = key.split('__')[0]
                # Handle cases like "pl001_0000/pl001_0001"
                if '/' in armor_id:
                    armor_id = armor_id.split('/')[-1]
                parsed[armor_id] = value

        return parsed

    except (json.JSONDecodeError, OSError) as e:
        print(f"Error loading armor database: {e}")
        return {}


def construct_export_path(
    game_path: str,
    armor_name: str,
    armor_part: str,
    gender: str,
    use_native_structure: bool = True,
    custom_path: Optional[str] = None
) -> str:
    """
    Construct the export path for MHW files.

    Args:
        game_path: Base game directory path.
        armor_name: Armor set ID (e.g., 'pl001_0000').
        armor_part: Armor piece type (e.g., 'leg', 'body').
        gender: Gender ('f' or 'm').
        use_native_structure: Whether to use nativePC folder structure.
        custom_path: Optional custom export path.

    Returns:
        Complete export path without file extension.

    Example:
        construct_export_path(
            'C:/MHW/',
            'pl001_0000',
            'body',
            'f'
        )
        # Returns: 'C:/MHW/nativePC/pl/f_equip/pl001_0000/body/mod/f_body001_0000'
    """
    # Determine root directory
    if custom_path and os.path.exists(custom_path):
        root_path = Path(custom_path)
    else:
        root_path = Path(game_path)

    # Construct native PC structure
    if use_native_structure:
        native_parts = [
            'nativePC',
            'pl',
            f'{gender}_equip',
            armor_name,
            armor_part,
            'mod'
        ]

        # Only add native structure if not already in path
        if 'nativePC' not in str(root_path):
            for part in native_parts:
                root_path = root_path / part

    # Construct filename (e.g., 'f_body001_0000')
    armor_number = armor_name[2:]  # Remove 'pl' prefix
    filename = f'{gender}_{armor_part}{armor_number}'

    return str(root_path / filename)


def ensure_directory_exists(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to create.

    Returns:
        True if directory exists or was created, False on error.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False


def open_directory_in_explorer(path: str) -> None:
    """
    Open a directory in the system file explorer.

    Args:
        path: Directory path to open.
    """
    if not os.path.exists(path):
        print(f"Directory does not exist: {path}")
        return

    try:
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif os.name == 'posix':  # Linux/Mac
            import subprocess
            if os.uname().sysname == 'Darwin':  # macOS
                subprocess.Popen(['open', path])
            else:  # Linux
                subprocess.Popen(['xdg-open', path])
    except Exception as e:
        print(f"Error opening directory {path}: {e}")


def validate_game_path(game_path: str) -> bool:
    """
    Validate that a path looks like a valid MHW game directory.

    Args:
        game_path: Path to validate.

    Returns:
        True if path appears valid, False otherwise.
    """
    if not game_path or not os.path.exists(game_path):
        return False

    # Check for common MHW directories/files
    game_path_obj = Path(game_path)
    indicators = [
        game_path_obj / 'nativePC',
        game_path_obj / 'MonsterHunterWorld.exe',
    ]

    return any(indicator.exists() for indicator in indicators)
