"""
UI module for MHW Set Organizer.

Contains panels, lists, and icon management for the addon UI.
"""

import bpy

# Import UI modules
from . import ui_lists
from . import list_operators
from . import main_panel
# from . import icons  # TODO: Implement if needed

# List of modules for registration
_modules = [
    ui_lists,
    list_operators,
    main_panel,
]


def register():
    """Register UI classes."""
    for module in _modules:
        if hasattr(module, 'register'):
            module.register()


def unregister():
    """Unregister UI classes."""
    for module in reversed(_modules):
        if hasattr(module, 'unregister'):
            module.unregister()
