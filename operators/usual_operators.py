import bpy,os,sys,bmesh
from bpy.props import EnumProperty,StringProperty,PointerProperty,IntProperty,BoolProperty
from bpy.types import Operator

sys.path.append("..")
from general_functions import all_heir,reeport,new_ob,upd_exp_path


class SimpleConfirmOperator(Operator):
    """Confirm deletion?"""
    bl_idname = "dpmhw.delete_collection"
    bl_label = "Remove"
    bl_options = {'REGISTER', 'INTERNAL'}
    del_how=StringProperty()
    col_path=StringProperty()
    col_num=IntProperty()
    header_remove=BoolProperty()
    keep_bones=BoolProperty()
    remove_vg=BoolProperty()
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        scene=context.scene
        mhw=scene.mhwsake
        # A bit rough way to delete a collection but idea was a universal delete button
        delwhat,delnum,delhow=self.col_path,self.col_num,self.del_how
        delwhat=eval(delwhat)
        to_rem=delwhat[delnum]
        to_rem_name=to_rem.name
        bremoved=[]
        if delhow=='delete_ctc':
            for o in to_rem.copy_src_track: #[a for a in to_rem.copy_src_track if a.is_new]:
                if o.ttype=='Bone' and self.keep_bones:continue
                if (o.ttype=='CTC' and not self.header_remove) or (o.o2.get('boneFunction') and o.bone_id<150):continue
                
                if o.o2!=None:
                    bremoved.append(o.o2.name)
                    bpy.data.objects.remove(o.o2)
                    
            self.report({'INFO'},'Removed a CTC Copy Set: %s'%to_rem.source.name)
            self.report({'INFO'},'Removed objects: %s'%bremoved)

        delwhat.remove(delnum)
        scene.update()
        
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.prop(self, "header_remove", text="Remove CTC Header Too?",icon='OUTLINER_OB_FORCE_FIELD')
        row=self.layout
        row.prop(self,"keep_bones",text="Keep ALL Bones?",icon='BONE_DATA')
        # row=self.layout
        # row.prop(self,'remove_vg',text='Remove Vertex Groups Associated?',icon='SNAP_VERTEX')

class CopyObjectChangeVG(Operator):
    """Copy a object, changing the vertex group names"""
    bl_idname = "dpmhw.copy_object"
    bl_label = "Copy Object"
    bl_options = {'REGISTER', 'INTERNAL'}
    addLR=BoolProperty(default=1,description='Will rename bones too, and vertex groups of other set objects!')
    remove_not_found=BoolProperty(default=1)
    copy_name=StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):

        scene=context.scene
        mhw=scene.mhwsake
        _set=mhw.export_set[mhw.oindex]
        source=_set.copy_obj_src
        obs=bpy.data.objects
        if source==None or _set.empty_root==None:
            self.report({'ERROR'},'No source, or no Armature selected for Active Set!')
            return {'FINISHED'}
        findroot=None
        findroots=[]
        for bo in source.vertex_groups:
            if obs.get(bo.name)!=None:
                findroot=obs[bo.name]
                while findroot!=None:
                    findroot=findroot.parent
                    findroots.append(findroot)
                if len(findroots)>2:
                    findroot=findroots[-2]
                break
        if findroot==None:
            self.report({'ERROR'},'Could not find Non-Bone root of source object skeleton.')
            return {'FINISHED'}
        tar_root=_set.empty_root
        tar_dic={a.get('boneFunction'):a for a in all_heir(tar_root)}
        source_dic={a.name:a.get('boneFunction') for a in all_heir(findroot)}
        onew=source.copy()
        onew.data=onew.data.copy()
        scene.update()
        old_vg_names={}
        for vg in onew.vertex_groups:
            vgn=vg.name
            oNum=source_dic.get(vgn)
            if oNum!=None and tar_dic.get(oNum):
                vg.name=vgg=tar_dic[oNum].name
                if self.addLR and oNum>=150:
                    print(oNum,vg.name)
                    if all(not vg.name.endswith(x) for x in ['.L','.R']):
                        tbone_X=tar_dic[oNum].matrix_world.to_translation()[0]
                        
                        vg.name=vg.name.replace('.R','').replace('.L','')
                        
                        if tbone_X<0:vg.name=vg.name+'.R'
                        elif tbone_X>0:vg.name=vg.name+'.L'
                        tar_dic[oNum].name=vg.name
                        old_vg_names[vgg]=vg.name
            elif self.remove_not_found:
                onew.vertex_groups.remove(group=vg)
        if old_vg_names!={}:
            for o in _set.eobjs:
                for vg in o.obje.vertex_groups:
                    if old_vg_names.get(vg.name):vg.name=old_vg_names[vg.name]
        scene.objects.link(onew)
        onew.hide=False
        onew.select=1
        onew.name='copy_%s'%onew.name if self.copy_name=='' else self.copy_name
        
        onew.data.name=onew.name
        self.report({'INFO'},'Sucesfully made a copy of %s as %s.'%(source.name,onew.name))
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.prop(self,'copy_name',icon='SYNTAX_OFF',text="Copy's Name")
        row = self.layout
        row.prop(self,'addLR',icon='STICKY_UVS_VERT',text='Add .R/.L to Bones/VGroups')
        row=self.layout
        row.prop(self,'remove_not_found',icon='CANCEL',text='Remove Bone-Not Found Grps')

class MHW_ImportManager(Operator): 
    """Import from Source, hold Shift to not prompt Options!"""
    bl_idname = "dpmhw.import_manager"
    bl_label = "Choose import options"

    func=StringProperty()
    var1=StringProperty()
    ext=StringProperty()
    all_options=['clear_scene','maximize_clipping','high_lod','import_header',
        'import_meshparts','import_unknown_mesh_props','import_textures','import_materials',
        'texture_path','import_skeleton','weight_format','override_defaults']
    extd={'MOD3':'.mod3','CCL':'.ccl','CTC':'.ctc'}
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        scene=context.scene
        

        _set=eval(self.var1)
        ext=self.ext
        upd_exp_path(_set,context)
        path=_set.import_path+ext
        
        if not os.path.exists(path): 
            
            return {'FINISHED'}
        if ext=='.mod3':
            bpy.ops.custom_import.import_mhw_mod3(filepath=path,
            clear_scene=_set.clear_scene,
            maximize_clipping=_set.maximize_clipping,
            high_lod=_set.high_lod,
            import_header=_set.import_header,
            import_meshparts=_set.import_meshparts,
            import_unknown_mesh_props=_set.import_unknown_mesh_props,
            import_textures=_set.import_textures,
            import_materials=_set.import_materials,
            texture_path=_set.texture_path,
            import_skeleton=_set.import_skeleton,
            weight_format=_set.weight_format,
            override_defaults=_set.override_defaults,
            
            )
        elif ext=='.ctc':
            bpy.ops.custom_import.import_mhw_ctc(
            filepath=path,
            missingFunctionBehaviour=_set.ctc_missingFunctionBehaviour)
        elif ext=='.ccl':
            bpy.ops.custom_import.import_mhw_ccl(
            filepath=path,
            missingFunctionBehaviour=ccl_missingFunctionBehaviour,
            scale=_set.ccl_scale
            )
        return {'FINISHED'}
    def invoke(self, context, event):
        self.ext=self.extd[self.func]
        if event.shift:
            return self.execute(context)
        else:
            return context.window_manager.invoke_props_dialog(self)
 
    def draw(self, context):
        scene=context.scene
        _set=eval(self.var1)
        if _set.clear_scene:
            layout=self.layout
            layout.label('NOTE: "clear scene" will erase all SETS data',icon='ERROR')
        layout=self.layout
        if self.ext=='.mod3':
            for v in self.all_options:
                row=layout.row()
                row.prop(_set,v)
        elif self.ext=='.ctc':
            row=layout.row()
            row.prop(_set,'ctc_missingFunctionBehaviour')
        else:
            row=layout.row()
            row.prop(_set,'ccl_scale')
            row=layout.row()
            row.prop(_set,'ccl_missingFunctionBehaviour')

class safeRemoveDoubles(Operator): 
    """Safely merge double vertices, press shift to auto choose Split Normals"""
    bl_idname = "dpmhw.safedoubleremove"
    bl_label = "Safely Remove Double Vertices"
    
    pres_methods=[['Normals Split','Use the split normals modifier','MOD_NORMALEDIT'],
    ['Normals Transfer','Use the transfer normals modifier','OBJECT_DATA']]
    tar_ob=StringProperty()
    pres_method=EnumProperty(items=[(a[0],a[0],a[1],a[2],x) for x,a in enumerate(pres_methods)])
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        if bpy.data.objects.get(self.tar_ob)!=None:
            scene=context.scene
            oob=bpy.data.objects[self.tar_ob]
            selsave=context.selected_objects
            aktsave=context.active_object
            

            me2=oob.data.copy()
            o2=new_ob(scene,'temporary_copydp',me2)
            bpy.ops.object.select_all(action='DESELECT')
            #stuff
            context.scene.objects.active=oob
            oob.select=1
            oob.select=1
            osave=[oob.hide,oob.hide_select]
            oob.hide=0
            oob.hide_select=0
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()
            bpy.ops.object.mode_set(mode='OBJECT')
            scene.update()
            mname='dpmhw_normals_pres'
            if self.pres_method=='Normals Split':
                m=oob.modifiers.new(mname,"NORMAL_EDIT")
                m.target=o2
                m.mode='DIRECTIONAL'
                m.use_direction_parallel=1
            elif self.pres_method=='Normals Transfer':
                m = oob.modifiers.new(mname,"DATA_TRANSFER")
                m.use_loop_data = True
                m.loop_mapping = "NEAREST_POLYNOR"
                m.data_types_loops = {'CUSTOM_NORMAL'}
                m.object = o2
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier=mname)
            
            #end
            for o in selsave:o.select=1
            context.scene.objects.active=aktsave
            bpy.data.objects.remove(o2)
            oob.hide,oob.hide_select=osave
            scene.update()
        return {'FINISHED'}
    def invoke(self, context, event):
        if event.shift:
            self.pres_method='Normals Transfer'
            return self.execute(context)
        else:
            return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        row=self.layout
        row.prop(self,'pres_method',text='Method')#,icon=self.pres_methods[self.pres_method[1]][2])

class SolveRepeatedUVs(Operator): 
    """Split mesh at UV Seams"""
    bl_idname = "dpmhw.uvsolves"
    bl_label = "Split UV Seam"
    
    tar_ob=StringProperty()

    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        if bpy.data.objects.get(self.tar_ob)!=None:
            oob=bpy.data.objects[self.tar_ob]
            selsave=context.selected_objects
            aktsave=context.active_object
            bpy.ops.object.select_all(action='DESELECT')
            context.scene.objects.active=oob
            oob.select=1
            osave=[oob.hide,oob.hide_select]
            oob.hide=0
            oob.hide_select=0
            bpy.ops.mod_tools.solve_uv_rep()
            for o in selsave:o.select=1
            context.scene.objects.active=aktsave
            oob.hide,oob.hide_select=osave
        return {'FINISHED'}
    def invoke(self, context, event):
        return self.execute(context)
    def draw(self, context):
        pass
cls=[SimpleConfirmOperator,CopyObjectChangeVG ,
SolveRepeatedUVs,safeRemoveDoubles,
MHW_ImportManager,
]
def register():
    for cl in cls:
        bpy.utils.register_class(cl)

def unregister():
    for cl in cls:
        bpy.utils.unregister_class(cl)
if __name__ == "operators.usual_operators":
    register()