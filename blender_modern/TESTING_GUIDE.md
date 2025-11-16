# MHW Set Organizer - Testing Guide

## Overview

This guide provides step-by-step instructions for testing the MHW Set Organizer addon in Blender 3.x/4.x.

## Prerequisites

### Required
- Blender 3.0 or higher (tested on 3.6+ and 4.x)
- Python 3.10+

### Optional (for Import Features)
- External MHW MOD3 importer addon
- External MHW CTC importer addon
- External MHW CCL importer addon
- Sample MHW armor data files

## Installation

### 1. Install the Addon

**Method 1: Install from ZIP**
1. Zip the entire `blender_modern/` directory
2. In Blender: Edit → Preferences → Add-ons → Install
3. Select the ZIP file
4. Enable "Import-Export: MHW Set Organizer"

**Method 2: Development Installation**
1. Copy `blender_modern/` to Blender's addons directory:
   - Windows: `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\`
   - Linux: `~/.config/blender/<version>/scripts/addons/`
   - macOS: `~/Library/Application Support/Blender/<version>/scripts/addons/`
2. Rename folder to `mhw_set_organizer` (no spaces)
3. In Blender: Edit → Preferences → Add-ons
4. Search for "MHW" and enable the addon

### 2. Verify Installation

After enabling, check the console for:
```
✓ MHW Set Organizer v1.0.0 registered successfully
  Properties: ✓ Complete
  Operators: ✓ Complete
  UI: ✓ Complete
  Ready to use!
```

### 3. Locate the Panel

1. Open 3D Viewport
2. Press `N` to open sidebar
3. Look for "MHW Tools" tab
4. You should see "MHW Set Organizer" panel

## Basic Functionality Tests

### Test 1: Settings Configuration

**Purpose:** Verify settings can be configured and saved.

**Steps:**
1. In MHW Set Organizer panel, find "Settings" section
2. Click the folder icon next to "Game" field
3. Set a valid directory path (doesn't need to be real MHW directory for this test)
4. Click the folder icon next to "Resource" field
5. Set another directory path
6. Click "Save Settings"
7. Close and reopen Blender
8. Load the same .blend file
9. Click "Load Settings"

**Expected Result:**
- Settings should persist after save
- Both paths should reload correctly
- Console shows "Settings saved" and "Settings loaded" messages

### Test 2: Export Set Management

**Purpose:** Test creating and managing export sets.

**Steps:**
1. In "Export Sets" section, click the `+` (Add) button
2. A new export set should appear in the list
3. Click on it to select it
4. In the name field, rename it to "Test Chest Armor"
5. Create a simple mesh object: Add → Mesh → Cube
6. In "Objects in Set" section, click `+` button
7. In the dropdown, select your cube object
8. Click the up/down arrows to test reordering sets
9. Create a second export set
10. Click `-` (Remove) button to delete it

**Expected Result:**
- Export sets can be created, renamed, and deleted
- Objects can be added to sets
- Set list shows proper names
- Active set is highlighted

### Test 3: Batch Export Sets

**Purpose:** Test batch export organization.

**Steps:**
1. Create 2-3 export sets (as in Test 2)
2. In "Batch Export" section header, click the arrow to expand it
3. Click `+` to create a new batch set
4. Name it "Full Armor Set"
5. In "Sets in Batch" list, click `+`
6. Select one of your export sets from the dropdown
7. Add another export set to the batch
8. Toggle the checkboxes for MOD3/CTC/CCL export types

**Expected Result:**
- Batch sets can be created and managed
- Export sets can be added to batches
- Export type toggles work properly
- List shows referenced export sets

### Test 4: Armor Configuration

**Purpose:** Test armor database and path generation.

**Steps:**
1. Select an export set
2. In "Set Settings" section, click the armor dropdown
3. You should see a list of armor IDs (loaded from armor_database.csv)
4. Select an armor (e.g., "Leather (pl001_0000)")
5. Set Armor Part dropdown to "body"
6. Set Gender to "Female"
7. Check the export path is generated automatically

**Expected Result:**
- Armor database loads correctly
- Dropdown shows armor names with IDs
- Export path updates automatically when settings change
- Path follows pattern: `game_path/.../pl/f_equip/pl001_0000/body/mod/f_bodypl001_0000`

### Test 5: Object View Modes

**Purpose:** Test the object list view mode selector.

**Steps:**
1. Create an export set with a mesh object
2. Give the mesh a shape key: In Object Data Properties → Shape Keys → `+`
3. In export set "Objects in Set" section, find "View" dropdown
4. Change view mode to "Shape Keys"
5. You should see shape key options appear for your object
6. Change to "Other" view mode
7. Different options should appear (hooks, preserve quad, etc.)

**Expected Result:**
- View mode selector changes visible options
- Shape key view shows shape key dropdown
- Other view shows additional mesh options
- Icons update appropriately

### Test 6: CTC Header Copier

**Purpose:** Test CTC header management interface.

**Steps:**
1. Create an empty: Add → Empty → Plain Axes
2. Select the empty, add custom property: Object Properties → Custom Properties → New
3. Name it "Type", set value to "CTC_HEADER"
4. In MHW panel, expand "CTC Header Copier" section
5. In the first dropdown, select your empty
6. Test the "Local Copy" button appears
7. Test the refresh external sources button

**Expected Result:**
- CTC Header section expands/collapses
- Objects with Type=CTC_HEADER are selectable
- Prepend/rename options are visible
- External refresh button is functional

### Test 7: UI Toggles and Panel State

**Purpose:** Verify all panel sections can be collapsed/expanded.

**Steps:**
1. Find the arrows next to each section header:
   - CTC Header Copier
   - Batch Export
   - Export Sets
2. Click each arrow to collapse the section
3. Click again to expand
4. Settings should persist within the session

**Expected Result:**
- All sections can collapse/collapse independently
- Arrow icons change (▶ when collapsed, ▼ when expanded)
- Content hides completely when collapsed
- Panel feels responsive and organized

## Advanced Feature Tests

### Test 8: Custom Export Paths

**Purpose:** Test custom path override functionality.

**Steps:**
1. Select an export set
2. In "Custom Path" field, enter a directory path
3. Enable "Use Custom Path" checkbox
4. Verify export path updates to use custom path
5. Disable "Use Custom Path"
6. Verify export path reverts to game path structure

**Expected Result:**
- Custom paths override default paths when enabled
- Checkbox properly toggles between modes
- Export path display updates correctly

### Test 9: Root and Header Assignment

**Purpose:** Test assigning skeleton roots and CTC headers.

**Steps:**
1. Create an empty for skeleton root
2. Create another empty with Type=CTC_HEADER custom property
3. In export set settings:
   - Assign first empty to "Root"
   - Assign second empty to "CTC Header"
4. Verify both assignments persist

**Expected Result:**
- Only empties appear in Root dropdown
- Only CTC headers appear in CTC Header dropdown
- Assignments save correctly

### Test 10: Object Export Toggles

**Purpose:** Test per-object export enable/disable.

**Steps:**
1. Add 3-4 objects to an export set
2. Click the radio button toggles next to each object
3. Some should show as enabled (filled circle), others disabled (empty circle)
4. In objects list, use the checkmark icons to:
   - Enable all objects
   - Disable all objects

**Expected Result:**
- Individual toggles work for each object
- Batch enable/disable buttons affect all objects
- Visual feedback is clear (filled vs empty circles)

## Testing Without External Importers

If you don't have the external MHW importer addons installed:

### Test 11: Import Error Handling

**Purpose:** Verify graceful error messages when importers are missing.

**Steps:**
1. Create an export set with a path configured
2. Click one of the import buttons: MOD3 / CTC / CCL
3. Observe the error message

**Expected Result:**
- Error message should state: "Operator module 'custom_import' not found. Is the MHW importer addon installed?"
- No crashes or Python tracebacks
- Error appears in Blender's info header or popup

### Test 12: Export Functionality (UI Only)

**Purpose:** Test export UI without actual file operations.

**Steps:**
1. Configure an export set with objects
2. Click Export buttons (MOD3/CTC/CCL)
3. If external exporters aren't available, verify error handling

**Expected Result:**
- Buttons are clickable
- Clear error messages if exporters missing
- No Blender crashes

## Testing With External Importers

If you have the MHW importer addons installed:

### Test 13: MOD3 Import

**Purpose:** Test importing MHW mesh files.

**Steps:**
1. Obtain a sample .mod3 file
2. Create export set
3. Set import path to the .mod3 file (without extension)
4. Click "MOD3" import button
5. Configure import options in dialog
6. Confirm import

**Expected Result:**
- Import dialog shows all MOD3 options
- File imports successfully
- Mesh appears in viewport
- Objects are added to export set (if option enabled)

### Test 14: CTC Import

**Purpose:** Test importing cloth physics files.

**Steps:**
1. Obtain a sample .ctc file
2. Configure export set with import path
3. Click "CTC" import button
4. Set missing bone function behavior
5. Confirm import

**Expected Result:**
- CTC objects import correctly
- Hierarchy is preserved
- Error handling works for missing bones

### Test 15: CCL Import

**Purpose:** Test importing collision capsules.

**Steps:**
1. Obtain a sample .ccl file
2. Configure import path
3. Click "CCL" import button
4. Set scale and missing function behavior
5. Confirm import

**Expected Result:**
- Collision capsules import correctly
- Scale is applied properly
- Missing bone handling works

### Test 16: Full Round-Trip

**Purpose:** Test import → modify → export workflow.

**Steps:**
1. Import a MOD3 file
2. Import its CTC file
3. Import its CCL file
4. Make modifications to meshes/physics
5. Export all three file types
6. Re-import and verify changes

**Expected Result:**
- All file types import correctly
- Modifications are preserved
- Export creates valid files
- Re-import shows modifications

## Performance and Stability Tests

### Test 17: Large Export Sets

**Purpose:** Test performance with many objects.

**Steps:**
1. Create an export set
2. Add 50+ objects to the set
3. Scroll through the object list
4. Toggle objects on/off
5. Change view modes

**Expected Result:**
- UI remains responsive
- List scrolling is smooth
- No noticeable lag

### Test 18: Multiple Export Sets

**Purpose:** Test with many export sets.

**Steps:**
1. Create 20+ export sets
2. Switch between them
3. Modify settings on each
4. Test batch operations

**Expected Result:**
- Switching sets is fast
- Settings are isolated per set
- No data corruption

### Test 19: Session Persistence

**Purpose:** Verify data persists across sessions.

**Steps:**
1. Create complex setup with:
   - Multiple export sets
   - Batch sets
   - Custom paths
   - Object assignments
2. Save .blend file
3. Close Blender
4. Reopen Blender
5. Open saved file

**Expected Result:**
- All export sets preserved
- All settings intact
- Object references still valid
- No "missing data" warnings

## Common Issues and Solutions

### Issue: Addon doesn't appear in sidebar

**Solution:**
- Press `N` to toggle sidebar visibility
- Check addon is enabled in Preferences
- Try switching to a different workspace and back
- Restart Blender

### Issue: "mhw_data not found" error

**Solution:**
- This means properties didn't register
- Check console for registration errors
- Verify all dependencies are met (Python 3.10+, Blender 3.0+)
- Try disabling and re-enabling addon

### Issue: Objects don't appear in dropdowns

**Solution:**
- Verify objects are the correct type (meshes for object list, empties for roots)
- Check object hasn't been deleted
- Refresh panel by switching to another object and back

### Issue: Export path is empty

**Solution:**
- Set Game Path in Settings section
- Select armor from armor database
- Set armor part and gender
- If still empty, check armor_database.csv loaded correctly

### Issue: Import buttons do nothing

**Solution:**
- Check external importer addons are installed
- Verify import path is set correctly
- Check console for error messages
- Ensure file exists at specified path

### Issue: Shape keys don't appear

**Solution:**
- Object must have mesh data
- Mesh must have shape keys added
- Set view mode to "Shape Keys"
- Check object is properly assigned in export set

## Test Checklist

Use this checklist to track testing progress:

- [ ] Installation successful
- [ ] Panel appears in sidebar
- [ ] Settings can be configured
- [ ] Settings save/load works
- [ ] Export sets can be created
- [ ] Export sets can be deleted
- [ ] Objects can be added to sets
- [ ] Object list displays correctly
- [ ] Batch sets can be created
- [ ] Export sets can be added to batches
- [ ] Armor database loads
- [ ] Armor selection updates path
- [ ] View modes change correctly
- [ ] Shape key view works
- [ ] CTC header section works
- [ ] Root object assignment works
- [ ] Custom paths work
- [ ] Export toggles work
- [ ] UI sections collapse/expand
- [ ] Error messages are helpful
- [ ] No crashes or tracebacks
- [ ] Data persists across sessions

## Reporting Issues

If you find bugs during testing:

1. **Check Console Output**
   - Window → Toggle System Console (Windows)
   - View console for Python errors

2. **Gather Information**
   - Blender version
   - Addon version
   - Steps to reproduce
   - Error messages
   - Screenshots if applicable

3. **Report on GitHub**
   - https://github.com/Sakenfor/MHW_SetOrganizer/issues
   - Include all gathered information
   - Attach .blend file if possible (without sensitive data)

## Next Steps

After basic testing:

1. **Test with Real Data**
   - Use actual MHW armor files
   - Test full import/export workflow
   - Verify game compatibility

2. **Stress Testing**
   - Very large export sets (100+ objects)
   - Complex CTC hierarchies
   - Multiple simultaneous batch exports

3. **Integration Testing**
   - Test with other Blender addons
   - Test in different Blender versions
   - Test on different operating systems

4. **User Acceptance Testing**
   - Have actual MHW modders test it
   - Gather feedback on workflow
   - Identify missing features

## Migration from Legacy Version

If migrating from the old `blender_2_79/` version:

### Data Migration

**WARNING:** The old and new versions use different property structures. You cannot simply open old .blend files.

**Migration Steps:**
1. In old Blender 2.79:
   - Document your export set configurations
   - Note all armor assignments
   - Export any work in progress

2. In new Blender 3.x/4.x:
   - Install new addon version
   - Recreate export sets manually
   - Re-assign objects and settings
   - Import your exported files

**What Doesn't Transfer:**
- Export set data structure changed
- Property names were standardized
- UI layout is reorganized

**What Still Works:**
- Same armor database (if using armor_database.csv)
- Same import/export file formats
- Same workflow concepts

## Conclusion

This testing guide covers the major functionality of the MHW Set Organizer addon. Thorough testing helps ensure stability and identifies any remaining issues before release.

For development testing, consider setting up automated tests using Blender's Python API and pytest-blender.
