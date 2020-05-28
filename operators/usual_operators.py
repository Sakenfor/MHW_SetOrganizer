import bpy,os,sys,bmesh
from bpy.props import EnumProperty,StringProperty,PointerProperty,IntProperty,BoolProperty
from bpy.types import Operator
from mathutils import Matrix,Vector
sys.path.append("..")
from general_functions import all_heir,reeport,new_ob,upd_exp_path
from general_functions import  find_mirror,ctc_copy_over_props,copy_props,weight_transfer,weight_clean
import random
chrs = 'abvgddjezzijklmnjoprstcufhccdzsh0123456789'
def rootfind(self,object):
    findroot=None
    findroots=[]
    obs=bpy.data.objects
    for bo in object.vertex_groups:
        if obs.get(bo.name)!=None:
            findroot=obs[bo.name]
            while findroot!=None:
                findroot=findroot.parent
                findroots.append(findroot)
            findroot=findroots[-2]
            break
    return findroot

class SimpleConfirmOperator(Operator):
    """Confirm deletion?"""
    bl_idname = "dpmhw.delete_collection"
    bl_label = "Remove"
    bl_options = {"REGISTER", "UNDO"} 
    
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
    """Copy/Replace a object, changing the vertex group names, copying properties if need, etc."""
    bl_idname = "dpmhw.copy_object"
    bl_label = "Copy Object"
    bl_options = {"REGISTER", "UNDO"} 
    
    addLR=BoolProperty(default=1,description='Will rename bones too, and vertex groups of other set objects!')
    remove_not_found=BoolProperty(default=1)
    copy_name=StringProperty()
    partial_vg=StringProperty()
    partial_mat=StringProperty()
    replace_mesh_only=BoolProperty()
    copy_props_too=BoolProperty(description='The Mesh Custom Properties')
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        scene=context.scene
        mhw=scene.mhwsake
        _set=mhw.export_set[mhw.oindex]
        source=_set.copy_obj_src
        obs=bpy.data.objects
        target=context.active_object
        if source==None or _set.empty_root==None:
            self.report({'ERROR'},'No source, or no Armature selected for Active Set!')
            return {'FINISHED'}
        findroot=rootfind(self,source)

        if findroot==None:
            self.report({'ERROR'},'Could not find Non-Bone root of source object skeleton.')
            return {'FINISHED'}
        tar_root=_set.empty_root
        tar_dic={a.get('boneFunction'):a for a in all_heir(tar_root)}
        source_dic={a.name:a.get('boneFunction') for a in all_heir(findroot)}
        #source_dic={a.get('boneFunction'):a.name for a in all_heir(findroot)}
        hsave=source.hide,source.hide_select
        source.hide,source.hide_select=0,0
        
        onew=onew_del=source.copy()
        onew.data=onew.data.copy()
        if onew.name not in scene.objects:
            scene.objects.link(onew)
            
        scene.update()
        if (self.partial_vg!='' or self.partial_mat!=''):
            bpy.ops.object.select_all(action='DESELECT')
            scene.objects.active=onew
            onew.select=1
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            byvg,bymat=0,0
            if self.partial_mat=='':
                onew.vertex_groups.active_index=onew.vertex_groups.find(self.partial_vg)
                bpy.ops.object.vertex_group_select()
                byvg=1
            else:
                onew.active_material_index=onew.data.materials.find(self.partial_mat)
                bpy.ops.object.material_slot_select()
                bymat=1
            bpy.ops.mesh.separate( type = 'SELECTED' )
            bpy.ops.object.mode_set(mode='OBJECT')
            onew=context.selected_objects[0]#context.active_object
            if bymat:
                for i,m in enumerate(onew.material_slots):
                    if m.name!=self.partial_mat:m.material=None
                    #Leaves a empty material slot, had issues with bpy.ops material slot remove.

            # if byvg:
                # onew.vertex_groups.remove(group=onew.vertex_groups[self.partial_vg])
            # else:
                
            bpy.data.objects.remove(onew_del)
        old_vg_names={}
        for vg in onew.vertex_groups:
            vgn=vg.name
            oNum=source_dic.get(vgn)
            if oNum!=None and tar_dic.get(oNum)!=None:
                vg.name=vgg=tar_dic[oNum].name
                if self.addLR and oNum>=150:
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
                if o.obje==None:continue
                for vg in o.obje.vertex_groups:
                    if old_vg_names.get(vg.name):vg.name=old_vg_names[vg.name]
        #scene.objects.link(onew)
        onew.hide=False
        onew.select=1
        if not self.replace_mesh_only:
            onew.name='copy_%s'%onew.name if self.copy_name=='' else self.copy_name
            onew.data.name=onew.name
            self.report({'INFO'},'Sucesfully made a copy of %s as %s.'%(source.name,onew.name))
        else:
            
            m2=onew.data.copy()
            if self.copy_props_too:
                copy_props(onew.data,m2) 
            else:
                copy_props(target.data,m2)
            m2.update()
            m2.name=target.name
            #if not self.copy_props_too:
            
                #Preserve Mesh Custom Properties on mesh swap
            target.data=m2
            
            for v in target.vertex_groups:target.vertex_groups.remove(group=v)
            target.data.update()
            weight_transfer(self,context,onew,target,vmap="TOPOLOGY")
            weight_clean(self,context,target)
            #copy_props(target,onew)
            # onn=target.name
            bpy.data.meshes.remove(onew.data)
            bpy.data.objects.remove(onew)
            scene.update()
            self.report({'INFO'},'Sucesfully replaced a mesh for %s'%(target.name))
            # onew.name=onn
        source.hide,source.hide_select=hsave
        
        
        self.partial_vg=''
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        scene=context.scene
        mhw=scene.mhwsake
        _set=mhw.export_set[mhw.oindex]
        source=_set.copy_obj_src
        layout = self.layout
        row=layout.row()
        row.prop(self,'replace_mesh_only',icon='MESH_DATA',text='Replace Mesh')
        row.prop(self,'copy_props_too',icon='PASTEDOWN',text='Copy Properties Too')
        row = self.layout
        row.prop(self,'copy_name',icon='SYNTAX_OFF',text="Copy's Name")
        row = self.layout
        row.prop(self,'addLR',icon='STICKY_UVS_VERT',text='Add .R/.L to Bones/VGroups')
        row=self.layout
        row.prop(self,'remove_not_found',icon='CANCEL',text='Remove Bone-Not Found Grps')
        row=self.layout
        row.label('partial mesh, by VG or Mat')
        row=self.layout 
        row.prop_search(self,'partial_vg',source,'vertex_groups',text='Copy part of mesh by vertex group')
        row=self.layout
        row.prop_search(self,'partial_mat',source.data,'materials',text='Copy part of mesh by vertex group')
        row=self.layout
        
        
class MHW_ImportManager(Operator): 
    """Import from Source, hold Shift to not prompt Options!"""
    bl_idname = "dpmhw.import_manager"
    bl_label = "Choose import options"
    bl_options = {"REGISTER", "UNDO"} 
    
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
    """Safely merge double vertices, hold Shift to choose last chosen options!"""
    bl_idname = "dpmhw.safedoubleremove"
    bl_label = "Safely Remove Double Vertices"
    bl_options = {"REGISTER", "UNDO"} 
    
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
            osave=[oob.hide,oob.hide_select]
            oob.hide=0
            oob.hide_select=0
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.reveal()
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
            #self.pres_method='Normals Transfer'
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
    bl_options = {"REGISTER", "UNDO"} 
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

def getArmature():
    arma = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    if len(arma) != 1:
        raise ValueError("Can't find canonical armature for the transfer to work on. There are %d/1 targets."%len(arma))
    return arma[0]
#Copied from MOD3 Importer/Exporter and slightly modified to use _set objects and empties

class SaketargetArmature(Operator):
    bl_idname = 'dpmhw.target_armature'
    bl_label = "Rename Groups to Armature Names"
    bl_description = "Renames every vertex group to it's Armature Target Name based on Current Bone Function ID."
    bl_options = {"REGISTER", "PRESET", "UNDO"}    

    def execute(self,context):
        fromEmpty = {}
        remapTable = {}
        scene=context.scene
        mhw=scene.mhwsake
        if len(mhw.export_set)==0:return {"FINISHED"}
        _set=mhw.export_set[mhw.oindex]
        if _set.empty_root==None:return{"FINISHED"}
        empties=all_heir(_set.empty_root)
        for ebone in [o for o in empties if o.get('boneFunction')!=None]:
            fromEmpty[ebone["boneFunction"]] = ebone
        armature = getArmature()
        for bone in armature.pose.bones:
            if "boneFunction" in bone and bone["boneFunction"] in fromEmpty:
                remapTable[fromEmpty[bone["boneFunction"]].name] = bone.name

        for mesh in [o.obje for o in _set.eobjs if o.obje !=None]:

            for group in mesh.vertex_groups:
                if group.name in remapTable:
                    group.name = remapTable[group.name]
            modifiers = mesh.modifiers
            if "Auxiliary Armature" not in modifiers:
                mod = modifiers.new("Auxiliary Armature","ARMATURE")
                mod.object = armature
            else:
                modifiers["Auxiliary Armature"].object = armature
        return {'FINISHED'}
#Copied from MOD3 Importer/Exporter and slightly modified to use _set objects and empties
class SaketargetEmpties(Operator):
    bl_idname = 'dpmhw.target_weights'
    bl_label = "Rename Groups to Empty Names"
    bl_description = "Renames every vertex group to it's Empty Target Name based on Current Bone Function ID."
    bl_options = {"REGISTER", "PRESET", "UNDO"}    

    def execute(self,context):
        scene=context.scene
        mhw=scene.mhwsake
        if len(mhw.export_set)==0:return {"FINISHED"}
        _set=mhw.export_set[mhw.oindex]
        if _set.empty_root==None:return{"FINISHED"}
        empties=all_heir(_set.empty_root)
        
        fromArmature = {}
        remapTable = {}
        armature = getArmature()
        
        for bone in armature.pose.bones:
            if "boneFunction" in bone:
                fromArmature[bone["boneFunction"]]=bone
        for ebone in [o for o in empties if o.get('boneFunction')!=None]:
            if ebone["boneFunction"] in fromArmature:
                remapTable[fromArmature[ebone["boneFunction"]].name] = ebone.name
        for mesh in [o.obje for o in _set.eobjs if o.obje !=None]:
            for group in mesh.vertex_groups:
                if group.name in remapTable:
                    group.name = remapTable[group.name]

        return {'FINISHED'}
       
class emptyVGrenamer(Operator): 
    """Rename Empties and VG adding .R .L"""
    bl_idname = "dpmhw.empty_vg_renamer"
    bl_label = "Rename Empty and VG"
    bl_options = {"REGISTER", "UNDO"} 
    
    uni_name=StringProperty()
    name_methods=[['Statyk Armature','Removes "Bone_" in bone names.','CONSTRAINT_BONE'],
    ['Raw Bone Names','What it says','BONE_DATA']]

    bone_naming=EnumProperty(items=[(a[0],a[0],a[1],a[2],x) for x,a in enumerate(name_methods)])

    target_what_choice=[['Selected Objects','...','MESH_CUBE'],
    ["All active set's objects",'...','OUTLINER_OB_GROUP_INSTANCE']]
    
    target_what=EnumProperty(items=[(a[0],a[0],a[1],a[2],x) for x,a in enumerate(target_what_choice)])

    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        scene=context.scene
        mhw=scene.mhwsake
        arma=mhw.vg_rename_arma
        
        if len(mhw.export_set)>0:
            _set=mhw.export_set[mhw.oindex]
        else:_set=False
        if _set and self.target_what=="All active set's objects":
            obj_pool=[a.obje for a in _set.eobjs if a.obje!=None and a.obje.name in scene.objects]
        elif self.target_what=='Selected Objects':
            obj_pool=context.selected_objects
        if obj_pool==[]:return {'FINISHED'}
        
        arma_dic={bo.get('boneFunction'):bo for bo in arma.pose.bones} if arma!=None else {}
        root=rootfind(self,obj_pool[0])
        empties=all_heir(root)
        emp_dic={em.get('boneFunction'):em for em in empties}
        ext_fix={'_L':'.L','_R':'.R'}
        b_locs,pairs={},{}
        nameadd=self.uni_name if self.uni_name!='' else ''.join(random.choice(chrs) for _ in range(6))
        nameadd+='_'
        
        for e in empties:
            if not e.get('boneFunction'):continue
            bf=e['boneFunction']
            bm=e.matrix_world.to_translation()
            b_locs[e]=[bm,Vector([-bm[0],bm[1],bm[2]])]
        for e in empties:
            if e.get('boneFunction')==None:continue
            bf=e['boneFunction']
            bone=arma_dic[bf] if arma_dic.get(bf)!=None else False
            
            ext='.R' if '.R' in e.name else '.L' if '.L' in e.name else ''
            #if ext=='':
            if bone:ext='_R' if bone.name.endswith('_R') else '_L' if bone.name.endswith('_L') else ext
            if ext=='':
                om=e.matrix_world
                tbone_X=om.to_translation()[0]
                if tbone_X<0:ext='.R'
                elif tbone_X>0:ext='.L'
                else:ext=''
            mirror=find_mirror(e,b_locs)
            obn='%s%s'%(nameadd,bf)
            if mirror:
                if pairs.get(mirror+bf):obn=pairs[mirror+bf]
                else:
                    obn='%s%s'%(nameadd,mirror+bf)
                    pairs[mirror+bf]=obn
            if bone:
                obn=nameadd+bone.name
                if ext!='':
                    obn=obn[:2] if obn.count(ext)>1 else obn.replace(ext,'')

            if ext_fix.get(ext):ext=ext_fix[ext]
            obn=obn+ext
            if self.bone_naming=='Statyk Armature':
                obn=obn.replace('Bone_','')
            #else:bnew=obn

            for ss in obj_pool:
                if ss.vertex_groups.get(e.name):
                    ss.vertex_groups[e.name].name=obn
            e.name=obn
        self.report({'INFO'},'Succesfully renamed vg/empties in: %s'%[a.name for a in obj_pool])
        return {'FINISHED'}
    def invoke(self, context, event):
        if context.active_object!=None:
            self.tar_ob=context.active_object.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        # row=self.layout
        scene=context.scene
        mhw=scene.mhwsake
        # row.prop_search(self,'tar_ob',context.scene,'objects',text='Target')
        row=self.layout
        row.prop(self,'bone_naming',text='Naming')
        row=self.layout
        row.prop(self,'target_what','Target(s)')
        row=self.layout
        row.prop(mhw,'vg_rename_arma','Arma')
        row=self.layout
        row.prop(self,'uni_name',text='PrependText')
        
class SetObjectsToggler(Operator):
    """Display all objects of this set (including ctc and arma), hiding all else, +Shift to not hide"""
    bl_idname = "dpmhw.set_objects_toggler"
    bl_label = "Show objects"
    bl_options = {"REGISTER", "UNDO"} 
    var1=StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        scene=context.scene
        _set=eval(self.var1)
        total_list=[_set.empty_root,_set.ctc_header]
        if not self.ev.shift:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.hide_view_set(unselected=True)

        total_list.extend([a.obje for a in _set.eobjs])
        for ob in [a for a in total_list if a!=None]:
            
            ob.hide=False
            if ob.parent==None:
                for _o in [a for a in all_heir(ob) if a!=None]:
                    _o.hide=False
                    
        return {'FINISHED'}
    def invoke(self, context, event):
        self.ev=event
        return self.execute(context)

def set_choose_dynamic(self,context):
    global enum_sets
    items=[(a[0],a[0],a[1],a[2],x) for x,a in enumerate( enum_sets)]
    return items
    
class updateUsersOfCTC(Operator):
    """Rename Empties and VG adding .R .L"""
    bl_idname = "dpmhw.update_ctc_users"
    bl_label = "Update users of this Set's CTC"
    bl_options = {"UNDO"} 
    
    var1=StringProperty()
    enum_sets=[]
    all_sets=[]
    set_choosing=EnumProperty(items=set_choose_dynamic)
    bones_too=BoolProperty(default=1)
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        scene=context.scene
        src_set=self.src_set
        if self.set_choosing=="All sets that use this set's CTC":
            set_target=[a for a in self.all_sets]
        else:
            sc_tar,set_tar=self.set_choosing.split('>>')
            set_target=[a for a in self.all_sets if  a[0].name==sc_tar and a[1].name==set_tar]
        for scene,se in set_target:
            for z in se.ctc_copy_src:
                if z.source==src_set.ctc_header:
                    ctc_copy_over_props(self,scene,z,bones_too=self.bones_too)
        scenes_updated={}
        #Guessing this is kinda neccesary, if one would batch update many sets, to not update pointlessly same scenes over again.
        for scene,se in set_target:
            if scenes_updated.get(scene)==None: 
                scene.update()
                scenes_updated[scene]=1
        self.enum_sets=[]
        self.all_sets=[]
        return {'FINISHED'}
        #def :
    def invoke(self, context, event):
        global enum_sets
        scene=context.scene
        self.src_set=eval(self.var1)
        enum_sets=[["All sets that use this set's CTC","","URL"]]
        for sce in bpy.data.scenes:
            for se in sce.mhwsake.export_set:
                if any(x.source==self.src_set.ctc_header for x in se.ctc_copy_src):
                #if se.ctc_header==self.src_set.ctc_header:
                    enum_sets.append(['%s>>%s'%(sce.name,se.name),'Choose this set','OOPS'])
                    self.all_sets.append([sce,se])
        #self.enum_sets=enum_sets
        if len(enum_sets)==1:
            self.report({'WARNING'},"This set's CTC Header is not used in any other set, through all scenes")
            return{'FINISHED'}
        set_choose_dynamic(self,context)
        
        # if context.active_object!=None:
            # self.tar_ob=context.active_object.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row=self.layout
        
        
        row.prop(self,'set_choosing',text='Target(s)')
        #row.prop_search(self,'tar_ob',context.scene,'objects',text='Target')
        row=self.layout
        row.prop(self,'bones_too',text='Copy bone matrices too?',icon='GROUP_BONE')
        
cls=[SimpleConfirmOperator,CopyObjectChangeVG ,
SolveRepeatedUVs,safeRemoveDoubles,
MHW_ImportManager,emptyVGrenamer,
updateUsersOfCTC,SetObjectsToggler,
SaketargetArmature,SaketargetEmpties,
]
def register():
    for cl in cls:
        bpy.utils.register_class(cl)

def unregister():
    for cl in cls:
        bpy.utils.unregister_class(cl)
if __name__ == "operators.usual_operators":
    register()