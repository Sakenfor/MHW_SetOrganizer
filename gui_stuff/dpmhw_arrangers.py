
import bpy
def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        for i in message.split('\n'):
            self.layout.label(i)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
class dpMHWSetObjArranger(bpy.types.Operator):
    """Move items up and down, add and remove"""
    bl_idname = "scene.dpmhw_obj_arranger"
    bl_label = "SetArranger"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}
    who=bpy.props.StringProperty()
    action = bpy.props.EnumProperty(
            items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ('BATCHADD', "Batch Add", ""),
            ))
            # ('FROMOLD', "Fromold", "")))   
    
    def invoke(self, context, event):
        scn = context.scene
        ET=scn.mhwsake
        scene=context.scene
        if len(ET.export_set)==0:return {"FINISHED"}
        aktse=_set=ET.export_set[ET.oindex]
        
        idx = aktse.oindex
        sob=context.active_object
        sobs=context.selected_objects
        try:
            item = aktse.eobjs[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(aktse.eobjs) - 1:
                item_next = aktse.eobjs[idx+1].name
                aktse.eobjs.move(idx, idx+1)
                _set.oindex += 1
                info = 'Item "%s" moved to position %d' % (item.name, _set.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = aktse.eobjs[idx-1].name
                aktse.eobjs.move(idx, idx-1)
                _set.oindex -= 1
                info = 'Item "%s" moved to position %d' % (item.name, _set.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (aktse.eobjs[idx].name)
                _set.oindex -= 1
                aktse.eobjs.remove(idx)
                self.report({'INFO'}, info)
            
        if self.action == 'ADD':   
            if not any(s.obje==sob for s in aktse.eobjs):
                item = aktse.eobjs.add()
                if sob!=None:
                    ina=sob.name
                else:
                    ina='New Object'
                item.name = ina
                item.obje=sob
                item.obj_type = "STRING"

                item.obj_id = len(aktse.eobjs)
                _set.oindex= len(aktse.eobjs)-1             
                info = '"%s" added to list' % (item.name)
                self.report({'INFO'}, info)
    
        elif self.action == 'BATCHADD':
            for o in [a for a in bpy.context.selected_objects if not any(s.obje==a for s in aktse.eobjs)]:
                item = aktse.eobjs.add()
                item.name = o.name
                item.obj_type = "STRING"
                # item.kind=o.type
                item.obje=o
                item.obj_id = len(aktse.eobjs)
                _set.oindex = len(aktse.eobjs)-1
                info = '"%s" added to list' % (item.name)
                self.report({'INFO'}, info)

        return {"FINISHED"}
class dpMHWSetArranger(bpy.types.Operator):
    """Move items up and down, add and remove"""
    bl_idname = "scene.dpmhw_set_arranger"
    bl_label = "SetArranger"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}
    who=bpy.props.StringProperty()
    action = bpy.props.EnumProperty(
            items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ))
    
    def invoke(self, context, event):
        scn = context.scene
        ET=aktse=scn.mhwsake
        scene=context.scene
        idx = ET.oindex
        sob=context.active_object
        sobs=context.selected_objects
        try:
            item = aktse.export_set[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(aktse.export_set) - 1:
                item_next = aktse.export_set[idx+1].name
                aktse.export_set.move(idx, idx+1)
                ET.oindex += 1
                info = 'Item "%s" moved to position %d' % (item.name, ET.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = aktse.export_set[idx-1].name
                aktse.export_set.move(idx, idx-1)
                ET.oindex -= 1
                info = 'Item "%s" moved to position %d' % (item.name, ET.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (aktse.export_set[idx].name)
                ET.oindex -= 1
                aktse.export_set.remove(idx)
                self.report({'INFO'}, info)
            
        if self.action == 'ADD':   
            
                item = aktse.export_set.add()
                item.name = 'New Set'
                item.obj_type = "STRING"
                ET.oindex= len(aktse.export_set)-1             
                info = '"%s" added to list' % (item.name)
                self.report({'INFO'}, info)
    
        return {"FINISHED"}

class dpMHW_drawSet(bpy.types.UIList):
    """Set drawing"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        in_set=[a for a in context.selected_objects if any(a==o.obje for o in item.eobjs if a!=None)]
        if in_set!=[]:layout.label(text='[%s]'%len(in_set),icon='MESH_CUBE')
        op=layout.operator('dpmhw.set_objects_toggler',text='',icon='GHOST_DISABLED')
        op.var1='scene.%s'%item.path_from_id()
    def invoke(self, context, event):        
        pass  
        
class dpMHW_drawObjSet(bpy.types.UIList):
    """Set objects drawing"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        ik='MESH_CAPSULE' if item.obje!=None and item.obje.get('Type') and item.obje['Type']=='CCL' else 'OBJECT_DATAMODE'
        mhw=bpy.context.scene.mhwsake
        _set=mhw.export_set[mhw.oindex]

        #l=layout.split(percentage=76,align=1)
        layout.prop_search(item,"obje",bpy.context.scene,'objects',icon=ik,text="")
        
        layout.prop(item, "export", text="", emboss=0, icon=['RADIOBUT_OFF','RADIOBUT_ON'][item.export],expand=0)

        if _set.more_obj_options:
            row=layout.row()
            # row.prop(item,'tag',text='Tag')
            row.prop(item,'preserve_quad',text='',icon='MOD_TRIANGULATE')
        if item.obje!=None:
            layout.operator('dpmhw.uvsolves',text='',icon='GROUP_UVS').tar_ob=item.obje.name
            layout.operator('dpmhw.safedoubleremove',text='',icon='VERTEXSEL').tar_ob=item.obje.name
    def invoke(self, context, event):        
        pass 


#--------------Blender Append --------------
class dpMHW_drawBlenderAppend(bpy.types.UIList):
    """Set drawing"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "path", text="", emboss=False, icon_value=icon)
    def invoke(self, context, event):        
        pass  
class dpMHWBlenderAppendArranger(bpy.types.Operator):
    """Move items up and down, add and remove"""
    bl_idname = "scene.dpmhw_blender_append_arranger"
    bl_label = "BlenderAppendArranger"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}
    who=bpy.props.StringProperty()
    action = bpy.props.EnumProperty(
            items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ))
    
    def invoke(self, context, event):
        scn = context.scene
        ET=aktse=scn.mhwsake
        scene=context.scene
        idx = ET.oindex_blend
        try:
            item = aktse.append_dirs[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(aktse.append_dirs) - 1:
                item_next = aktse.append_dirs[idx+1].name
                aktse.append_dirs.move(idx, idx+1)
                ET.oindex_blend += 1
                info = 'Item "%s" moved to position %d' % (item.name, ET.oindex_blend + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = aktse.append_dirs[idx-1].name
                aktse.append_dirs.move(idx, idx-1)
                ET.oindex_blend -= 1
                info = 'Item "%s" moved to position %d' % (item.name, ET.oindex_blend + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (aktse.append_dirs[idx].name)
                ET.oindex_blend -= 1
                aktse.append_dirs.remove(idx)
                self.report({'INFO'}, info)
            
        if self.action == 'ADD':   
            
                item = aktse.append_dirs.add()
                item.name = 'New Set'
                item.obj_type = "STRING"
                ET.oindex_blend= len(aktse.append_dirs)-1             
                info = '"%s" added to list' % (item.name)
                self.report({'INFO'}, info)
    
        return {"FINISHED"}

#--------------Sets of Sets --------------
class dpMHWSetOfSetsArranger(bpy.types.Operator):
    """Move items up and down, add and remove"""
    bl_idname = "scene.dpmhw_setofsets_arranger"
    bl_label = "SetArranger"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}
    who=bpy.props.StringProperty()
    action = bpy.props.EnumProperty(
            items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ))
    
    def invoke(self, context, event):
        scn = context.scene
        ET=aktse=scn.mhwsake
        scene=context.scene
        idx = ET.oindex2
        try:
            item = aktse.export_setofsets[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(aktse.export_setofsets) - 1:
                item_next = aktse.export_setofsets[idx+1].name
                aktse.export_setofsets.move(idx, idx+1)
                ET.oindex2 += 1
                info = 'Item "%s" moved to position %d' % (item.name, ET.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = aktse.export_setofsets[idx-1].name
                aktse.export_setofsets.move(idx, idx-1)
                ET.oindex2 -= 1
                info = 'Item "%s" moved to position %d' % (item.name, ET.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (aktse.export_setofsets[idx].name)
                ET.oindex2 -= 1
                aktse.export_setofsets.remove(idx)
                self.report({'INFO'}, info)
            
        if self.action == 'ADD':   
            
                item = aktse.export_setofsets.add()
                item.name = 'New Set'
                item.obj_type = "STRING"
                ET.oindex2= len(aktse.export_setofsets)-1             
                info = '"%s" added to list' % (item.name)
                self.report({'INFO'}, info)


        return {"FINISHED"}


class dpMHWSetOfSetsObjArranger(bpy.types.Operator):
    """Move items up and down, add and remove"""
    bl_idname = "scene.dpmhw_setofsets_obj_arranger"
    bl_label = "SetArranger"
    bl_description = "Move items up and down, add and remove"
    bl_options = {'REGISTER'}
    who=bpy.props.StringProperty()
    action = bpy.props.EnumProperty(
            items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ))
    
    def invoke(self, context, event):
        scn = context.scene
        ET=scn.mhwsake
        scene=context.scene
        if len(ET.export_set)==0:return {"FINISHED"}
        aktse=_set=ET.export_setofsets[ET.oindex2]
        
        idx = aktse.oindex
        # sob=context.active_object
        # sobs=context.selected_objects
        try:
            item = aktse.eobjs[idx]
        except IndexError:
            pass
        else:
            if self.action == 'DOWN' and idx < len(aktse.eobjs) - 1:
                item_next = aktse.eobjs[idx+1].name
                aktse.eobjs.move(idx, idx+1)
                _set.oindex += 1
                info = 'Item "%s" moved to position %d' % (item.name, _set.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'UP' and idx >= 1:
                item_prev = aktse.eobjs[idx-1].name
                aktse.eobjs.move(idx, idx-1)
                _set.oindex -= 1
                info = 'Item "%s" moved to position %d' % (item.name, _set.oindex + 1)
                self.report({'INFO'}, info)

            elif self.action == 'REMOVE':
                info = 'Item "%s" removed from list' % (aktse.eobjs[idx].name)
                _set.oindex -= 1
                aktse.eobjs.remove(idx)
                self.report({'INFO'}, info)
            
        if self.action == 'ADD':   
                item = aktse.eobjs.add()

                item.name = 'Choose a Set'

                item.obj_type = "STRING"

                item.obj_id = len(aktse.eobjs)
                _set.oindex= len(aktse.eobjs)-1             
                info = '"%s" added to list' % (item.name)
                self.report({'INFO'}, info)

        return {"FINISHED"}


class dpMHW_drawSetOfSets(bpy.types.UIList):
    """Set drawing"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon_value=icon)
    def invoke(self, context, event):        
        pass  
class dpMHW_drawSetOfSetsObjs(bpy.types.UIList):
    """Set objects drawing"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        #ik='MESH_CAPSULE' if item.obje!=None and item.obje.get('Type') and item.obje['Type']=='CCL' else 'OBJECT_DATAMODE'
        mhw=bpy.context.scene.mhwsake
        _set=mhw.export_set[mhw.oindex]

        l=layout.split(percentage=76,align=1)
        #l.prop(item,"obje",text="")
        l.prop_search(item,'name',mhw,'export_set')
        layout.prop(item, "export", text="", emboss=0, icon=['RADIOBUT_OFF','RADIOBUT_ON'][item.export],expand=0)

    def invoke(self, context, event):        
        pass 

cls=[dpMHWSetObjArranger,dpMHWSetArranger,dpMHW_drawSet,dpMHW_drawObjSet,
dpMHW_drawSetOfSets,dpMHW_drawSetOfSetsObjs,dpMHWSetOfSetsArranger,dpMHWSetOfSetsObjArranger,
dpMHWBlenderAppendArranger,dpMHW_drawBlenderAppend]

def register():
    for cl in cls:
        bpy.utils.register_class(cl)
def unregister():
    for cl in cls:
        bpy.utils.unregister_class(cl)
if __name__ == "gui_stuff.dpmhw_arrangers":
    register()
