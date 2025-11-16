# MHW Set Organizer - Modernized for Blender 3.x/4.x

This is a refactored version of the MHW Set Organizer addon, updated to support modern Blender versions (3.0+) with improved code quality and maintainability.

## Key Improvements

### Blender API Updates
- ✅ Updated to Blender 3.x/4.x API
- ✅ Removed deprecated `bpy.types.Scene` properties
- ✅ Modern registration system with `bpy.utils.register_class()`
- ✅ Updated UI layouts and property definitions

### Code Quality
- ✅ Proper module organization (properties, operators, ui, core, utils)
- ✅ Type hints for better IDE support
- ✅ Comprehensive docstrings
- ✅ PEP 8 compliant formatting
- ✅ Proper exception handling
- ✅ Constants instead of magic numbers
- ✅ No `eval()` usage
- ✅ Removed global state where possible

### Structure
```
blender_modern/
├── __init__.py          # Main addon entry point
├── addon_config.py      # Constants and configuration
├── properties/          # Blender property groups
├── operators/           # All operator classes
├── ui/                  # UI panels and lists
├── core/                # Business logic (export, CTC, weights)
├── utils/               # Helper functions
├── data/                # JSON data files
└── icons/               # UI icons
```

## Installation

1. Copy the `blender_modern` folder to your Blender addons directory
2. Rename it to `mhw_set_organizer`
3. Enable in Blender Preferences → Add-ons

## Compatibility

- **Blender Version**: 3.0+ (tested on 3.6 and 4.0)
- **Python Version**: 3.10+
- **Dependencies**:
  - Mod3-MHW-Importer (by AsteriskAmpersand)
  - CTC-MHW-Editor (by AsteriskAmpersand)

## Migration from Legacy Version

See [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) for details on changes and how to migrate your workflows.

## Development

This version follows modern Python best practices:
- Type hints for all functions
- Docstrings in Google style
- Separated concerns (UI/Logic/Data)
- Testable components
- Clear naming conventions

## Credits

**Original Author**: Sakenfor (dp16)
**Modernization**: 2024 refactoring to Blender 4.x standards
