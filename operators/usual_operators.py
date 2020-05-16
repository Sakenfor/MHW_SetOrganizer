import bpy
from bpy.props import StringProperty,PointerProperty,IntProperty
from bpy.types import Operator

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
            for o in [a for a in to_rem.copy_src_track if a.is_new]:
                if o.o2!=None:bpy.data.objects.remove(o.o2)

        delwhat.remove(delnum)
        scene.update()

 

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

cls=[SimpleConfirmOperator,

]

def register():
    for cl in cls:
        bpy.utils.register_class(cl)

def unregister():
    for cl in cls:
        bpy.utils.unregister_class(cl)
if __name__ == "operators.usual_operators":
    register()