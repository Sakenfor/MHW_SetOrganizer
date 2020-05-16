import bpy,glob
def all_heir(ob, levels=10):
    oreturn=[]
    def recurse(ob, parent, depth):
        if depth > levels: 
            return
        oreturn.append(ob)
        for child in ob.children:
            recurse(child, ob,  depth + 1)
    recurse(ob, ob.parent, 0)
    return oreturn
def find_col_index(name,collection):
    for i,st in enumerate(collection):
        if st.name==name:
            return i
    return None
def copy_props(sors,tar):
    for k,v in sors.items():tar[k]=v
    
def copy_various_props(o,o2):
    copy_props(o,o2)
    o2.empty_draw_type=o.empty_draw_type
    o2.show_bounds=o.show_bounds
    o2.show_x_ray=o.show_x_ray

def new_ob(name,mesh=None):
    o=bpy.data.objects.new(name,mesh)
    bpy.context.scene.objects.link(o)
    return o
def header_copy_poll(self,object):
    return object.get('Type') and object['Type']=='CTC'

def has_att(ob,name,str1=None):
    return ob.get(name) and (ob[name]==str1 and str1!=None)

def goto_set_dir(context):
    scene=context.scene
    mhw=scene.mhwsake
    _set=mhw.export_set[mhw.oindex]
    
    os.startfile(path)
    #todo, button that opens a directory of chosen set

def ctc_edit_col_edit(self,context,var1):
    mhw=context.scene.mhwsake
    ctc_num,set_num,toggle=var1.split('|')
    _set=mhw.export_set[int(set_num)]
    _ctcset=_set.ctc_copy_src[int(ctc_num)]
    if 'Hide' ==toggle or 'Show'==toggle:
        for i in _ctcset.copy_src_track:i.edit_view=hideshow[toggle]
    elif toggle=='Update':
        for i in _ctcset.copy_src_track:
            i.name=i.o2.name

def reload_external_ctc(self,context):
    scene=context.scene
    mhw=scene.mhwsake
    while len(mhw.extctc_src)>0:mhw.extctc_src.remove(0)
    thisblend=bpy.data.filepath.split('\\')[-1]
    for f in mhw.append_dirs:
        
        for blend in glob.glob(f.path+'/*.blend'):
            if  thisblend in blend:continue
            with bpy.data.libraries.load(blend, link=True) as (data_from, data_to):
                data_to.objects = [name for name in data_from.objects]
            for ob in data_to.objects:
                #if ob.library==None:continue
                if ob.get('Type') and ob['Type']=='CTC':
                    blendname=blend.split('\\')[-1]
                    uniquename=blendname+'__'+ob.name
                    if mhw.extctc_src.get(uniquename)==None:
                       
                        ext=mhw.extctc_src.add()
                        ext.name=uniquename
                        ext.folder=f.path
                        ext.blend=blend
                   #bpy.context.scene.objects.link(obj) # Blender 2.7x



types_icons={'CTC_*_Frame':'ORTHO',
'CTC':'LOGIC',
'CTC_Chain':'LINKED',
'Bone':'BONE_DATA',
}

editable_types=['CTC_*_Frame','CTC','CTC_Chain','Bone']

all_types=['CTC_*_Frame','CTC','CTC_Chain','CTC_Node']

prop_edit_list={'CTC_*_Frame':
['Fixed End','radius','unknownFloatSet000'],

'CTC':
['Dampening','Gravity Multiplier','Low Wind Effect',
'Medium Wind Effect','Strong Wind Effect'],

'CTC_Chain':
['Snapping','Tension','Weightiness','Cone of Motion',
'Wind Multiplier','Chain Length','CCL Collision'],
'Bone':
['boneFunction','unkn2'],
'CTC_Node':[]
}
props_icons={'Snapping':'FORCE_HARMONIC',
'Tension':'FORCE_TURBULENCE',
'Wind Multiplier':'FORCE_WIND',

}

type_sort_order=['CTC_Chain','CTC','CTC_*_Frame','Bone']

target_lambda={'Edit Source':lambda x:x.caster,'Edit Copies':lambda x:x.o2}

hideshow={'Hide':0,'Show':1}

regular_ctc_names={'CTC_*_Frame':'Frame',
'CTC':'Header',
'CTC_Chain':'Chain',
'CTC_Node':'Node'}
def ob_in_track(mhw,caster,add_src=None,armature=None,o2=None,report=None):
    if add_src==None:
        for i,o in enumerate(mhw.copy_src_track):

            if o.caster==caster and o.caster!=None:

                if o.armature==armature and armature!=None:
                    #if report!=None:
                        #report.report({'INFO'},str(o.obje)+' =? '+str(ob)+' > '+str(o.armature))
                        #report.report({'INFO'},str(o.armature)+' =? '+str(armature) )
                    
                    return o if o.o2!=None else None
    else:
        nob=mhw.copy_src_track.add()
        nob.caster=caster

        if add_src!=None:nob.ctc_src=add_src
        if armature!=None:nob.armature=armature
        if o2!=None:
            nob.o2=o2
            nob.name=o2.name
        if caster.get('Type') and caster['Type'] in editable_types:
            nob.ttype=caster['Type']
        elif caster.get('boneFunction'):nob.ttype='Bone'

        #print('New object track %s'%ob.name)
        return nob
    return None
infos={'obj_info':
'''You can put capsules in objects list too.
Use black dot to toggle export on/off of per object.
Can freely change scene object names without editing list names again. 
(same goes for 'Root' and 'CTC_header')

Use ctrl+scroll to go through objects, or click between name and the dot
to select a object. 
'''
,'scenes_reload':
'''
Refresh settings and armor 'numbers'(folder names),
use it if you create new scene to update the settings.
'''
,'append_native':
'''
This will append nativePC\..etc.. to the set's
Custom Path too, when export is ran from Batch Export.

If Set's Custom Path has nativePC on, and 'UsePerSetCustompath' is on,
nativePC will be added, even if this toggle is off.
'''
,'ctc_copy':
'''
This text will be prepended to all CTC and Bones that will be copied,

Best to use some text to easier tell apart the CTC's.
'''
,'ctc_edit_update':
'''
Update internal names of ctc edit collection, useful for the "Pick" prop search only ATM.

Can freely edit object names with that being said.
'''
 }
