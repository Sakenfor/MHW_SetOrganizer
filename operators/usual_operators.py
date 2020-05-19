import bpy,os,sys
from bpy.props import StringProperty,PointerProperty,IntProperty,BoolProperty
from bpy.types import Operator

sys.path.append("..")
from general_functions import all_heir
def remove_ctc_copy(self,context,var1):
    pass


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
        if delhow=='delete_ctc':
            for o in to_rem.copy_src_track: #[a for a in to_rem.copy_src_track if a.is_new]:
                if (o.ttype=='Header' and not self.header_remove) or (o.ttype=='Bone' and o.bone_id<150):continue
                if o.ttype=='Bone' and self.keep_bones:continue
                if o.o2!=None:bpy.data.objects.remove(o.o2)
            self.report({'INFO'},'Removed a CTC Copy Set: %s'%to_rem.source.name)

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
                if self.addLR:
                    if not all(vg.name.endswith(x) for x in ['.L','.R']):
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
cls=[SimpleConfirmOperator,CopyObjectChangeVG

]

def register():
    for cl in cls:
        bpy.utils.register_class(cl)

def unregister():
    for cl in cls:
        bpy.utils.unregister_class(cl)
if __name__ == "operators.usual_operators":
    register()