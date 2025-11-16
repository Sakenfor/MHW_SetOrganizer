# Blender 2.79 Backward Compatibility Analysis

## Critical Incompatibilities

### 1. **F-Strings (Python 3.6+ feature)**
**Problem:** Blender 2.79 uses Python 3.5, which doesn't support f-strings.
**Current code:** `f"Export: {export_set.name}"`
**Would need:** `"Export: {}".format(export_set.name)` or `"Export: %s" % export_set.name`
**Impact:** ~300+ f-strings throughout the codebase

### 2. **Context Overrides**
**Problem:** `context.temp_override()` doesn't exist in 2.79
**Current code:**
```python
with bpy.context.temp_override(object=target):
    bpy.ops.object.modifier_apply(modifier=mod.name)
```
**Would need:**
```python
# Blender 2.79 syntax
override = bpy.context.copy()
override['object'] = target
bpy.ops.object.modifier_apply(override, modifier=mod.name)
```
**Impact:** 3 locations in core logic

### 3. **UI Panel Region**
**Problem:** Sidebar changed from TOOLS to UI
**Current code:** `bl_region_type = 'UI'`
**Would need:** `bl_region_type = 'TOOLS'` for 2.79
**Impact:** 1 location (main panel)

### 4. **Pathlib Usage**
**Status:** ✓ Compatible (Python 3.4+)
**No changes needed**

### 5. **Type Hints**
**Status:** ✓ Mostly compatible
**Python 3.5 supports basic type hints**

---

## Compatibility Solutions

### Option 1: Version Detection Layer (Recommended)
Create a compatibility module that abstracts differences.

**Pros:**
- Single codebase
- Clean separation of compatibility logic
- Easy to maintain

**Cons:**
- Some overhead
- Need to test on both versions

**Implementation:**
```python
# blender_modern/compat.py
import bpy

# Detect Blender version
BLENDER_VERSION = bpy.app.version
IS_LEGACY = BLENDER_VERSION < (2, 80, 0)
IS_MODERN = BLENDER_VERSION >= (3, 0, 0)

# Region type
SIDEBAR_REGION = 'TOOLS' if IS_LEGACY else 'UI'

# Context override wrapper
def context_override(context, **kwargs):
    """Unified context override for all Blender versions."""
    if IS_LEGACY:
        # 2.79 style: return dict
        override = context.copy()
        override.update(kwargs)
        return override
    else:
        # 3.x+ style: return context manager
        return context.temp_override(**kwargs)

# String formatting helper
def fstr(*args, **kwargs):
    """F-string replacement for Python 3.5."""
    # Just use .format() universally
    pass
```

**Usage:**
```python
from ..compat import SIDEBAR_REGION, context_override

class MHW_PT_MainPanel(Panel):
    bl_region_type = SIDEBAR_REGION  # Adapts to version

def apply_modifier(context, obj, mod_name):
    if IS_LEGACY:
        override = context_override(context, object=obj)
        bpy.ops.object.modifier_apply(override, modifier=mod_name)
    else:
        with context_override(context, object=obj):
            bpy.ops.object.modifier_apply(modifier=mod_name)
```

### Option 2: Automated Conversion
Use a script to generate two versions from one source.

**Pros:**
- Each version is optimized
- No runtime overhead

**Cons:**
- Need to maintain conversion script
- More complex build process

### Option 3: Separate Branches
Keep `blender_2_79/` and `blender_modern/` separate.

**Pros:**
- Clean, no compatibility code
- Each fully optimized

**Cons:**
- Duplicate work for new features
- Two codebases to maintain

---

## Effort Estimation

### To make current code work on 2.79:

1. **F-string conversion:** ~4-6 hours
   - 300+ replacements
   - Can be automated with regex
   - Need manual review

2. **Context override fixes:** ~1 hour
   - 3 locations
   - Need version detection

3. **UI region fix:** ~15 minutes
   - 1 location
   - Simple version check

4. **Testing:** ~4-8 hours
   - Install Blender 2.79
   - Test all features
   - Fix edge cases

**Total:** ~10-16 hours of work

---

## Recommendation

### **Don't make it backward compatible with 2.79.**

**Reasons:**

1. **Blender 2.79 is 7 years old (2018)**
   - Blender LTS policy: support only recent versions
   - Community has mostly moved on
   - Modern features (3.x/4.x) are significant improvements

2. **Python 3.5 is EOL (End of Life)**
   - No security updates since 2020
   - Modern libraries don't support it

3. **Maintenance burden**
   - Every new feature needs compatibility layer
   - Testing on multiple versions
   - Harder to use modern Python features

4. **External tools are also outdated**
   - Mod3-MHW-Importer hasn't been updated in 3-5 years
   - Likely doesn't work properly on 2.79 either
   - Users on 2.79 probably have the old addon working

5. **Better use of time**
   - Implement actual improvements (collections, validation, etc.)
   - Update external tool integration
   - Add new features users want

### **Alternative: Hybrid Approach**

**Keep both versions separate:**
- `blender_2_79/` - Original, frozen, for legacy users
- `blender_modern/` - New, actively developed, 3.x/4.x only

**Migration path:**
- Users on 2.79: Use old version, still works
- Users upgrading to modern Blender: Use new version
- Provide migration guide (export settings, recreate sets)

---

## What Users Actually Need

Instead of backward compatibility, focus on:

1. **Clear version documentation**
   - README stating: "Blender 3.0+ required"
   - Legacy version still available for 2.79

2. **Migration guide**
   - How to export work from 2.79
   - How to set up in modern Blender
   - Settings transfer instructions

3. **Modern features**
   - Collections-based organization
   - Better validation
   - Improved workflows
   - Integration with modern Blender

4. **Update external tool support**
   - Check if Mod3-MHW-Importer works on 3.x/4.x
   - Update operator calls if needed
   - Better error handling

---

## Counter-Argument: When Backward Compatibility Makes Sense

Only consider 2.79 compatibility if:
- [ ] Large user base still on 2.79 (unlikely after 7 years)
- [ ] External tools only work on 2.79 (need to verify)
- [ ] Mod projects still require 2.79 (very unlikely)
- [ ] Users explicitly request it

None of these seem likely.

---

## Conclusion

**Recommendation: Keep modern version (3.x/4.x) separate.**

**Instead, invest time in:**
1. Verifying external tools work on modern Blender
2. Implementing high-value improvements
3. Creating excellent documentation
4. Making migration from legacy version easy

**If you still want backward compatibility:**
- Use Option 1 (compatibility layer)
- Start with automated f-string conversion
- Test thoroughly on both versions
- Be prepared for ongoing maintenance burden
