"""
Icon management for MHW Set Organizer.

Handles loading and accessing custom icons used in the UI.
"""

import bpy
import bpy.utils.previews
from pathlib import Path

# Global icon preview collection
_icon_previews = None


def get_addon_icons_path() -> Path:
    """Get the path to the icons directory."""
    return Path(__file__).parent.parent / 'icons'


def get_icon_id(icon_name: str) -> int:
    """
    Get the icon ID for a custom icon.

    Args:
        icon_name: Name of the icon (without .png extension).

    Returns:
        Icon ID for use in UI, or 0 if not found.

    Example:
        >>> icon_id = get_icon_id('export')
        >>> row.operator('mhw.export', icon_value=icon_id)
    """
    global _icon_previews

    if _icon_previews is None:
        return 0

    if icon_name not in _icon_previews:
        print(f"Warning: Icon '{icon_name}' not found")
        return 0

    return _icon_previews[icon_name].icon_id


def register():
    """Load all custom icons."""
    global _icon_previews

    _icon_previews = bpy.utils.previews.new()

    icons_path = get_addon_icons_path()

    if not icons_path.exists():
        print(f"Warning: Icons directory not found at {icons_path}")
        return

    # Load all PNG files from icons directory
    for icon_file in icons_path.glob('*.png'):
        icon_name = icon_file.stem  # Filename without extension
        try:
            _icon_previews.load(icon_name, str(icon_file), 'IMAGE')
        except Exception as e:
            print(f"Error loading icon {icon_file}: {e}")

    print(f"✓ Loaded {len(_icon_previews)} custom icons")


def unregister():
    """Remove all custom icons."""
    global _icon_previews

    if _icon_previews:
        bpy.utils.previews.remove(_icon_previews)
        _icon_previews = None
