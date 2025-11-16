"""
Auto Backup operators for MHW Set Organizer.

Provides automatic backup functionality before risky operations.
"""

import bpy
from bpy.types import Operator
from pathlib import Path
import shutil
from datetime import datetime


def create_backup(context, operation_name: str) -> bool:
    """
    Create a timestamped backup of the current file.

    Args:
        context: Blender context
        operation_name: Name of the operation (for backup filename)

    Returns:
        True if backup was created successfully, False otherwise
    """
    # Check if current file is saved
    if not bpy.data.filepath:
        print("Cannot create backup: File is not saved")
        return False

    try:
        source_path = Path(bpy.data.filepath)

        # Get backup directory from preferences
        mhw = context.scene.mhw_data
        backup_dir = Path(mhw.backup_directory) if mhw.backup_directory else source_path.parent / "backups"

        # Create backup directory if it doesn't exist
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"{source_path.stem}_{timestamp}_before_{operation_name}.blend"
        backup_path = backup_dir / backup_name

        # Create backup
        shutil.copy2(source_path, backup_path)

        # Cleanup old backups
        cleanup_old_backups(backup_dir, mhw.backup_max_count)

        print(f"✓ Backup created: {backup_path.name}")
        return True

    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        return False


def cleanup_old_backups(backup_dir: Path, max_count: int):
    """
    Remove old backups, keeping only the most recent ones.

    Args:
        backup_dir: Directory containing backups
        max_count: Maximum number of backups to keep
    """
    try:
        # Get all backup files, sorted by modification time (newest first)
        backups = sorted(
            backup_dir.glob("*.blend"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove excess backups
        for backup in backups[max_count:]:
            backup.unlink()
            print(f"  Removed old backup: {backup.name}")

    except Exception as e:
        print(f"Warning: Failed to cleanup old backups: {e}")


def should_create_backup(context, operation_name: str) -> bool:
    """
    Check if backup should be created for this operation.

    Args:
        context: Blender context
        operation_name: Name of the operation

    Returns:
        True if backup should be created
    """
    mhw = context.scene.mhw_data

    if not mhw.backup_enabled:
        return False

    # Check operation-specific settings
    operation_map = {
        'batch_ops': mhw.backup_before_batch,
        'ctc_copy': mhw.backup_before_ctc,
        'weight_transfer': mhw.backup_before_weights,
    }

    return operation_map.get(operation_name, False)


class MHW_OT_CreateBackup(Operator):
    """Create a manual backup of the current file"""
    bl_idname = "mhw.create_backup"
    bl_label = "Create Backup"
    bl_options = {'REGISTER'}

    operation_name: bpy.props.StringProperty(
        name="Operation Name",
        description="Name of the operation (for backup filename)",
        default="manual",
    )

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return bpy.data.filepath != ""

    def execute(self, context):
        """Create backup."""
        if create_backup(context, self.operation_name):
            self.report({'INFO'}, f"Backup created successfully")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to create backup (file may not be saved)")
            return {'CANCELLED'}


class MHW_OT_RestoreBackup(Operator):
    """Restore from a backup file"""
    bl_idname = "mhw.restore_backup"
    bl_label = "Restore from Backup"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        name="Backup File",
        description="Path to backup file to restore",
        subtype='FILE_PATH',
    )

    def execute(self, context):
        """Restore backup."""
        if not self.filepath:
            self.report({'ERROR'}, "No backup file selected")
            return {'CANCELLED'}

        try:
            # Open the backup file
            bpy.ops.wm.open_mainfile(filepath=self.filepath)
            self.report({'INFO'}, f"Restored from backup")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to restore backup: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        """Show file browser."""
        mhw = context.scene.mhw_data
        backup_dir = Path(mhw.backup_directory) if mhw.backup_directory else Path(bpy.data.filepath).parent / "backups"

        if backup_dir.exists():
            self.filepath = str(backup_dir)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MHW_OT_ViewBackups(Operator):
    """Open backup directory in file browser"""
    bl_idname = "mhw.view_backups"
    bl_label = "View Backups"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return bpy.data.filepath != ""

    def execute(self, context):
        """Open backup directory."""
        import subprocess
        import platform

        mhw = context.scene.mhw_data
        backup_dir = Path(mhw.backup_directory) if mhw.backup_directory else Path(bpy.data.filepath).parent / "backups"

        # Create directory if it doesn't exist
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Open directory in file browser
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.Popen(['explorer', str(backup_dir)])
            elif system == "Darwin":  # macOS
                subprocess.Popen(['open', str(backup_dir)])
            else:  # Linux
                subprocess.Popen(['xdg-open', str(backup_dir)])

            self.report({'INFO'}, f"Opened backup directory")
            return {'FINISHED'}
        except Exception as e:
            self.report({'WARNING'}, f"Could not open directory: {e}")
            self.report({'INFO'}, f"Backup directory: {backup_dir}")
            return {'FINISHED'}


class MHW_OT_CleanupBackups(Operator):
    """Remove old backups beyond the maximum count"""
    bl_idname = "mhw.cleanup_backups"
    bl_label = "Cleanup Old Backups"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        """Check if operator can run."""
        return bpy.data.filepath != ""

    def execute(self, context):
        """Cleanup old backups."""
        mhw = context.scene.mhw_data
        backup_dir = Path(mhw.backup_directory) if mhw.backup_directory else Path(bpy.data.filepath).parent / "backups"

        if not backup_dir.exists():
            self.report({'INFO'}, "No backup directory found")
            return {'CANCELLED'}

        # Get backup count before cleanup
        backups_before = len(list(backup_dir.glob("*.blend")))

        # Cleanup
        cleanup_old_backups(backup_dir, mhw.backup_max_count)

        # Get backup count after cleanup
        backups_after = len(list(backup_dir.glob("*.blend")))
        removed = backups_before - backups_after

        if removed > 0:
            self.report({'INFO'}, f"Removed {removed} old backup(s)")
        else:
            self.report({'INFO'}, "No backups needed cleanup")

        return {'FINISHED'}


# Classes to register
classes = (
    MHW_OT_CreateBackup,
    MHW_OT_RestoreBackup,
    MHW_OT_ViewBackups,
    MHW_OT_CleanupBackups,
)


def register():
    """Register backup operators."""
    for cls in classes:
        bpy.utils.register_class(cls)

    print("  Backup System: ✓ Registered")


def unregister():
    """Unregister backup operators."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
