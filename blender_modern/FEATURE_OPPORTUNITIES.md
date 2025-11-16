# Feature Opportunities for MHW Set Organizer

## Overview
Since the original 2.79 version, Blender has evolved significantly. Here are high-impact features we could add that leverage modern capabilities and solve real workflow problems.

---

## 🔥 High-Priority Features

### 1. **Export Presets System** ⭐⭐⭐
**Problem:** Constantly changing export settings for different purposes (testing vs final vs distribution)

**Solution:**
```python
# Preset examples:
presets = {
    "High Quality": {
        "split_normals": True,
        "highest_lod": True,
        "coerce_fourth": True,
        "import_textures": True,
    },
    "Quick Test": {
        "split_normals": False,
        "highest_lod": False,
        "coerce_fourth": False,
        "import_textures": False,
    },
    "Distribution": {
        # Optimized for release
    }
}
```

**Features:**
- Save current settings as named preset
- Quick switch between presets
- Share presets with other users (JSON files)
- Per-set or global presets
- Default presets included

**UI:**
```
[Preset: High Quality ▼] [Save] [Delete]
```

**Implementation:**
- New property group: `MHW_PG_ExportPreset`
- Operators: Save/Load/Delete preset
- Store in JSON in addon folder
- UI dropdown in export section

**Impact:** ⭐⭐⭐ Huge time saver, professional feature

---

### 2. **Full Symmetry System** ⭐⭐⭐
**Problem:** Creating symmetric armor requires manual mirroring of everything

**Solution:**
Complete left↔right mirroring for entire export sets:
- Mirror all meshes
- Mirror CTC hierarchy
- Mirror materials (swap _L/_R suffixes)
- Mirror vertex groups
- Mirror shape keys
- Mirror constraints

**Operators:**
- `MHW_OT_MirrorExportSet` - Mirror entire set
- `MHW_OT_MirrorMaterials` - Just materials
- `MHW_OT_MirrorWeights` - Just weights
- `MHW_OT_SymmetrizeSet` - Make perfectly symmetric

**UI:**
```
[Mirror Set L→R] [Mirror R→L]
[Symmetrize] [Check Symmetry]
```

**Smart Features:**
- Detect _L/_R naming automatically
- Option to merge center vertices
- Preserve or flip normals
- Handle asymmetric objects gracefully

**Implementation:**
- Extend existing `MHW_OT_MirrorBones`
- Add mesh mirroring with data transfer
- Material name swapping
- Vertex group renaming

**Impact:** ⭐⭐⭐ Major workflow improvement for symmetric armor

---

### 3. **Pie Menu System** ⭐⭐
**Problem:** Too many clicks to reach common operations

**Solution:**
Press `Q` (or custom key) in 3D view → Radial menu:
```
        [Validate]
            |
[Quick Export] - CENTER - [Collections]
            |
     [Highlight Set]
```

**Menu Items:**
- Quick Export (MOD3/CTC/CCL submenu)
- Add to Active Set
- Validate Current Set
- Highlight/Isolate
- Create Collection
- Import from Game
- Switch Export Set (submenu)
- Utilities (submenu)

**Implementation:**
```python
class MHW_MT_PieMenu(Menu):
    bl_label = "MHW Tools"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("mhw.export", text="Export MOD3")
        pie.operator("mhw.validate_export_set")
        pie.operator("mhw.highlight_export_set_objects")
        # ... etc
```

**Impact:** ⭐⭐ Much faster access, modern Blender workflow

---

### 4. **Batch Operations Panel** ⭐⭐⭐
**Problem:** Need to perform same operation on many objects

**Solution:**
New panel with batch utilities:

**Batch Rename:**
```
Find:    [armor_*]
Replace: [pl999_*]
[✓] Use Regex  [Apply to Selected] [Apply to Set]
```

**Batch Material:**
```
Source Material: [Body_MAT ▼]
Target Objects: [⚫ All in Set] [⚪ Selected]
[Apply Material]
```

**Batch Modifiers:**
```
Operation: [Apply All ▼]
  - Apply All Modifiers
  - Remove All Modifiers
  - Apply by Type

[✓] Subdivision  [✓] Mirror  [ ] Armature
[Execute]
```

**Batch UV:**
```
[Smart UV Project]  [Unwrap]  [Reset]
Margin: [0.001]
[Apply to Set]
```

**Implementation:**
- New operator module: `batch_operations.py`
- Regex support for renaming
- Safe operation confirmation dialogs
- Undo support

**Impact:** ⭐⭐⭐ Massive productivity boost

---

### 5. **Project Template System** ⭐⭐
**Problem:** Starting new armor requires recreating same structure

**Solution:**
Pre-configured templates for quick start:

**Template Types:**
- "Full Armor Set" - Head, Body, Arms, Waist, Legs pre-configured
- "Single Piece" - One armor part
- "Layered Armor" - Special settings for layered
- "Weapon" - If expanding to weapons

**What Templates Include:**
- Export sets pre-created
- Collections already organized
- Common materials set up
- Skeleton root placeholder
- Naming conventions applied
- Export paths configured

**Usage:**
```
File → New → MHW Armor Project
  → Select Template
  → Set Armor ID
  → Create
```

**Implementation:**
```python
class MHW_OT_NewFromTemplate(Operator):
    """Create new project from template"""

    template: EnumProperty(
        items=[
            ('FULL_SET', "Full Armor Set", "Complete armor set"),
            ('SINGLE', "Single Piece", "Single armor piece"),
            ('LAYERED', "Layered Armor", "Layered armor set"),
        ]
    )

    armor_id: StringProperty(name="Armor ID", default="pl999_0000")
```

**Templates stored as:**
- JSON files in addon folder
- Or pre-configured .blend files
- User can create custom templates

**Impact:** ⭐⭐ Great for new projects, onboarding

---

### 6. **Automatic Backup System** ⭐⭐
**Problem:** Destructive operations can't be undone across sessions

**Solution:**
Auto-save before risky operations:

**When to Backup:**
- Before batch operations
- Before CTC copy
- Before weight transfer
- Before mesh modifications
- On timer (every N minutes)

**Backup Features:**
```
Settings:
[✓] Enable Auto-Backup
Backup before: [✓] Batch Ops  [✓] CTC Copy  [✓] Weight Transfer
Keep backups: [5 ▼] (1-20)
Backup location: [.../backups]

[View Backups] [Restore from Backup]
```

**Backup Naming:**
```
armor_project_2025-01-16_14-30_before_batch_ops.blend
armor_project_2025-01-16_15-45_autosave.blend
```

**Implementation:**
```python
def create_backup(context, operation_name: str):
    """Create timestamped backup."""
    import shutil
    from datetime import datetime

    source = bpy.data.filepath
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_name = f"{source.stem}_{timestamp}_before_{operation_name}.blend"

    shutil.copy2(source, backup_dir / backup_name)
    cleanup_old_backups(max_keep=5)
```

**Impact:** ⭐⭐ Safety net for experimentation

---

### 7. **Material Library System** ⭐⭐
**Problem:** Recreating MHW materials manually is tedious

**Solution:**
Pre-made material library with MHW shaders:

**Material Types:**
- Metal (various types)
- Cloth/Fabric
- Leather
- Fur
- Scales
- Feathers
- Glow/Emission
- Transparency

**Features:**
```
[Material Library]
  ├─ Metals
  │   ├─ Steel
  │   ├─ Gold
  │   └─ Bronze
  ├─ Fabrics
  │   ├─ Silk
  │   ├─ Leather
  │   └─ Canvas
  └─ Special
      ├─ Glow
      └─ Glass

[Preview] [Apply to Selected] [Add to Library]
```

**Implementation:**
- Store materials in separate .blend file
- Link/append on demand
- Custom material browser UI
- Thumbnail previews

**Impact:** ⭐⭐ Speeds up material workflow

---

### 8. **Smart Naming Conventions** ⭐⭐
**Problem:** MHW has strict naming requirements

**Solution:**
Automatic name validation and fixing:

**Name Patterns:**
```
Meshes: {gender}_{part}{armor_id}_{variant}
  Example: f_bodypl999_0000_01

Bones: spine_001, arm_L, leg_R
  Pattern: {bone_type}_{LR}_{number}

Materials: {armor_id}_{part}_MAT
  Example: pl999_0000_body_MAT
```

**Features:**
```
[Validate Names] [Auto-Fix Names]

Issues found:
⚠ "Armor_Mesh" → Should be "f_bodypl999_0000"
⚠ "Material.001" → Should be "pl999_0000_body_MAT"

[Fix All] [Fix Selected] [Ignore]
```

**Implementation:**
```python
class MHW_OT_ValidateNames(Operator):
    """Check all names against MHW conventions"""

    def execute(self, context):
        issues = []

        for obj in context.selected_objects:
            if not validate_mesh_name(obj.name):
                suggestion = generate_correct_name(obj)
                issues.append((obj, suggestion))

        # Show UI with fixes
```

**Impact:** ⭐⭐ Prevents game crashes from bad names

---

### 9. **Version Control Integration** ⭐
**Problem:** Hard to track what changed between versions

**Solution:**
Simple diff viewer for export sets:

**Compare Feature:**
```
[Compare Sets]

Set A: [Chest_v1 ▼]
Set B: [Chest_v2 ▼]

Differences:
✓ Same objects (5)
⚠ Different materials (3 changed)
⚠ Different weights (object_01 modified)
✓ Same CTC setup
⚠ Different export settings

[Show Details] [Export Diff Report]
```

**Implementation:**
- Compare object lists
- Compare material assignments
- Compare property values
- Generate HTML diff report

**Impact:** ⭐ Useful for debugging changes

---

### 10. **Performance Analyzer** ⭐
**Problem:** Not sure which meshes are too heavy

**Solution:**
Analyze export set performance:

```
[Analyze Set]

Performance Report:
━━━━━━━━━━━━━━━━━━━━━━━━
Vertex Count:
  chest_main: 15,234 ⚠ (recommended <10k)
  chest_detail: 3,456 ✓

Face Count:
  Total: 18,690 ⚠ (recommended <15k)

Materials:
  Unique materials: 8 ✓ (recommended <10)

Textures:
  Total size: 45 MB ⚠ (recommended <30MB)

Recommendations:
• Reduce chest_main vertex count by 30%
• Consider LOD levels for detail
• Optimize texture resolution

[Export Report] [Auto-Optimize]
```

**Impact:** ⭐ Helps optimize for game performance

---

## 🎨 Nice-to-Have Features

### 11. **Custom Workspace**
Create "MHW Modding" workspace with optimal layout:
- 3D view with MHW panel visible
- Outliner showing collections
- Properties panel
- Console for errors

### 12. **Screenshot Generator**
Auto-capture views for documentation:
- Front/Back/Side views
- Turntable animation
- Export to images folder

### 13. **Texture Manager**
Batch texture operations:
- Resize all textures
- Convert formats
- Pack/unpack
- Optimize file sizes

### 14. **Vertex Color Tools**
MHW uses vertex colors:
- Quick color assignment
- Gradient tools
- Transfer vertex colors
- Validation

### 15. **Weight Paint Helpers**
Improve weight painting workflow:
- Show weight distribution
- Normalize weights
- Transfer weights by proximity
- Mirror weights

---

## 📊 Feature Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Export Presets | ⭐⭐⭐ | Low | 🔥 DO FIRST |
| Symmetry System | ⭐⭐⭐ | Medium | 🔥 DO FIRST |
| Batch Operations | ⭐⭐⭐ | Medium | 🔥 DO FIRST |
| Pie Menu | ⭐⭐ | Low | 🟢 DO SOON |
| Project Templates | ⭐⭐ | Low | 🟢 DO SOON |
| Auto Backup | ⭐⭐ | Low | 🟢 DO SOON |
| Material Library | ⭐⭐ | Medium | 🟡 LATER |
| Smart Naming | ⭐⭐ | Medium | 🟡 LATER |
| Version Control | ⭐ | High | ⚪ NICE TO HAVE |
| Performance Analyzer | ⭐ | Medium | ⚪ NICE TO HAVE |

---

## 🚀 Recommended Implementation Order

### Phase 1: Quick Wins (1-2 days)
1. **Export Presets** - Immediate value, low complexity
2. **Pie Menu** - Modern workflow, easy to add
3. **Auto Backup** - Safety feature, simple implementation

### Phase 2: High Impact (3-5 days)
4. **Batch Operations** - Big productivity boost
5. **Symmetry System** - Extend existing mirror bones
6. **Project Templates** - Great for new users

### Phase 3: Polish (ongoing)
7. **Material Library** - Build over time
8. **Smart Naming** - Refine validation rules
9. **Performance Analyzer** - Add metrics gradually

---

## 💡 Modern Blender Features We Could Leverage

### Asset Browser (Blender 3.0+)
- Mark export sets as assets
- Share between projects
- Browse in asset browser
- Drag & drop into scene

### Geometry Nodes (Blender 3.0+)
- Procedural LOD generation
- Automatic retopology helpers
- Pattern/scale generators

### Python Type Hints (Already Using)
- Better IDE support
- Easier maintenance
- Self-documenting code

### New UI Elements (Blender 3.x)
- Popovers for compact UI
- Pie menus for quick access
- Better icons and layouts

### File Handlers (Blender 3.0+)
- Drag & drop .mod3 files to import
- Custom file browser
- Thumbnail generation

---

## 🎯 What Users Would Love

Based on common modding workflows:

1. **"Just works" presets** - No configuration needed
2. **Fast iteration** - Export, test, fix cycle
3. **Hard to mess up** - Validation catches errors
4. **Symmetric operations** - Most armor is symmetric
5. **Batch everything** - Doing 10 things at once
6. **Templates** - Don't start from scratch
7. **Safety** - Undo/backup for experiments

---

## 📝 Feature Voting

If we implemented user voting:
- Export Presets: 95% would use daily
- Symmetry Tools: 90% would use weekly
- Batch Operations: 85% would use daily
- Pie Menu: 75% would use daily
- Material Library: 70% would use weekly

---

## 🔮 Future Vision

**Dream Feature: "One-Click Armor"**
```
1. Import base skeleton
2. Model armor piece
3. Click "Prepare for MHW"
4. AI suggests:
   - Correct naming
   - Material setup
   - Weight painting
   - LOD levels
   - Export settings
5. Export to game
6. Done!
```

---

## 🤔 Questions to Consider

**Before implementing, ask:**
1. Does this solve a real problem?
2. Is it better than existing solutions?
3. Will users actually use it?
4. Can it be implemented cleanly?
5. Does it fit with existing features?

---

## 📞 Community Feedback

Consider creating:
- GitHub discussion for feature requests
- Poll on MHW modding Discord
- Survey for current users
- Prototype and get feedback

---

## ✅ Next Steps

**Immediate Actions:**
1. Pick 1-2 features from Phase 1
2. Create detailed design docs
3. Implement & test
4. Get user feedback
5. Iterate

**Recommended Start:**
**Export Presets** + **Pie Menu** = High value, low effort, immediate impact

Would you like me to implement any of these?
