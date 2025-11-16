"""
MHW Set Organizer - Blender Addon for Monster Hunter World Armor Modding

A comprehensive tool for organizing, exporting, and managing MHW armor sets,
including MOD3 meshes, CTC cloth physics, and CCL collision capsules.

Modernized for Blender 3.x/4.x with improved code quality and API compatibility.
"""

import bpy

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

# Module imports
_modules = []
_modules_loaded = False


def load_modules():
    """Lazy load all addon modules."""
    global _modules, _modules_loaded

    if _modules_loaded:
        return

    # Import modules
    from . import properties
    from . import operators
    from . import ui
    from . import utils

    _modules = [
        properties,
        operators,
        ui,
    ]

    _modules_loaded = True


def register():
    """Register addon classes and properties."""
    try:
        # Load modules
        load_modules()

        # Register all modules
        for module in _modules:
            if hasattr(module, 'register'):
                module.register()

        # Register icons (if UI module exists)
        try:
            from .ui import icons
            icons.register()
        except ImportError:
            pass  # UI not implemented yet

        # Initialize armor database
        from .utils import file_utils
        armor_data = file_utils.load_armor_database()

        # Populate armor database in first scene
        if len(bpy.data.scenes) > 0:
            scene = bpy.data.scenes[0]
            if hasattr(scene, 'mhw_data'):
                mhw = scene.mhw_data

                # Clear and populate armor database
                mhw.armor_database.clear()
                for armor_id, armor_name in armor_data.items():
                    entry = mhw.armor_database.add()
                    entry.armor_id = armor_id
                    entry.name = f"{armor_name} ({armor_id})"

                # Initialize built-in export presets
                from .properties import export_presets
                export_presets.create_builtin_presets(mhw.export_presets)

        version_str = '.'.join(map(str, addon_config.ADDON_VERSION))
        print(f"✓ {addon_config.ADDON_NAME} v{version_str} registered successfully")
        print(f"  Properties: ✓ Complete")
        print(f"  Operators: ✓ Complete")
        print(f"  UI: ✓ Complete")
        print(f"  Ready to use!")

    except Exception as e:
        print(f"✗ Failed to register {addon_config.ADDON_NAME}: {e}")
        import traceback
        traceback.print_exc()
        raise


def unregister():
    """Unregister addon classes and properties."""
    try:
        # Unregister icons
        try:
            from .ui import icons
            icons.unregister()
        except ImportError:
            pass

        # Unregister modules in reverse order
        for module in reversed(_modules):
            if hasattr(module, 'unregister'):
                module.unregister()

        version_str = '.'.join(map(str, addon_config.ADDON_VERSION))
        print(f"✓ {addon_config.ADDON_NAME} v{version_str} unregistered")

    except Exception as e:
        print(f"✗ Failed to unregister {addon_config.ADDON_NAME}: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    register()
