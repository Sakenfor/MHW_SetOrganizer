"""
MHW Set Organizer - Blender Addon for Monster Hunter World Armor Modding

A comprehensive tool for organizing, exporting, and managing MHW armor sets,
including MOD3 meshes, CTC cloth physics, and CCL collision capsules.

Modernized for Blender 3.x/4.x with improved code quality and API compatibility.
"""

import bpy
from bpy.props import PointerProperty

from . import addon_config

bl_info = {
    "name": addon_config.ADDON_NAME,
    "author": addon_config.ADDON_AUTHOR,
    "version": addon_config.ADDON_VERSION,
    "blender": addon_config.BLENDER_VERSION_MIN,
    "location": "View3D > MHW Tools",
    "description": "Easy export and organizing of MHW armor sets, objects, and CTC physics",
    "warning": "",
    "doc_url": "https://github.com/Sakenfor/MHW_SetOrganizer/wiki",
    "category": "Import-Export",
}

# Module imports - these will be imported when modules are created
# Import order matters for registration
_modules = []

def register_modules():
    """Import and register all addon modules."""
    global _modules

    # Import all modules
    from . import properties
    from . import operators
    from . import ui
    from . import utils

    _modules = [
        properties,
        operators,
        ui,
    ]

    # Register all modules
    for module in _modules:
        if hasattr(module, 'register'):
            module.register()


def unregister_modules():
    """Unregister all addon modules."""
    # Unregister in reverse order
    for module in reversed(_modules):
        if hasattr(module, 'unregister'):
            module.unregister()


def register():
    """Register addon classes and properties."""
    try:
        register_modules()

        # Register icons
        from .ui import icons
        icons.register()

        print(f"✓ {addon_config.ADDON_NAME} v{'.'.join(map(str, addon_config.ADDON_VERSION))} registered successfully")

    except Exception as e:
        print(f"✗ Failed to register {addon_config.ADDON_NAME}: {e}")
        raise


def unregister():
    """Unregister addon classes and properties."""
    try:
        # Unregister icons
        from .ui import icons
        icons.unregister()

        unregister_modules()

        print(f"✓ {addon_config.ADDON_NAME} unregistered")

    except Exception as e:
        print(f"✗ Failed to unregister {addon_config.ADDON_NAME}: {e}")
        raise


if __name__ == "__main__":
    register()
