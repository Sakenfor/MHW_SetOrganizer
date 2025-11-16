"""
Operators module for MHW Set Organizer.

Contains all operator classes for user actions.
"""

import bpy

# Import operator modules
from . import export_ops
from . import import_ops
from . import ctc_ops
from . import utility_ops
from . import quick_actions
from . import validation_ops
from . import collection_ops

# List of modules for registration
_modules = [
    export_ops,
    import_ops,
    ctc_ops,
    utility_ops,
    quick_actions,
    validation_ops,
    collection_ops,
]


def register():
    """Register operator classes."""
    for module in _modules:
        if hasattr(module, 'register'):
            module.register()


def unregister():
    """Unregister operator classes."""
    for module in reversed(_modules):
        if hasattr(module, 'unregister'):
            module.unregister()

