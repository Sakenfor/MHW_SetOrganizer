

import bpy,os,sys,json,glob,importlib
from bpy.app.handlers import persistent


base_dir = os.path.dirname(os.path.realpath(__file__))

if not base_dir in sys.path:sys.path.append(base_dir)
#
from gui_stuff import dpmhw_arrangers
from gui_stuff.dpmhw_arrangers import *
importlib.reload(dpmhw_arrangers)

from bpy.props import EnumProperty,StringProperty,BoolProperty,FloatProperty,IntProperty,CollectionProperty,PointerProperty
from bpy.types import PropertyGroup
json_savepath=base_dir+'\\MhwSettings.json'

armor_parts_enum=['leg','wst','arm','body','helm']


class mhwExpSetObj(PropertyGroup):
    name=StringProperty()
    export=BoolProperty(default=1)
    obje=PointerProperty(type=bpy.types.Object)

class mhwExpSet(PropertyGroup):
    name=StringProperty()
    oindex=IntProperty()
    eobjs=CollectionProperty(type=mhwExpSetObj)
    nativePCappend=BoolProperty()
    armor_name=StringProperty()
    armor_part=EnumProperty(items=[(a,a,a) for a in armor_parts_enum])
    gender=EnumProperty(items=[(a,a,a) for a in ['f','m']],default='f')
    empty_root=PointerProperty(type=bpy.types.Object)
    ctc_header=PointerProperty(type=bpy.types.Object)
    
    custom_export_path=StringProperty(subtype='FILE_PATH')
    use_custom_path=BoolProperty()
    
    split_normals = BoolProperty(
        name = "Use Custom Normals",
        description = "Use split/custom normals instead of Blender autogenerated normals.",
        default = True)
    highest_lod = BoolProperty(
        name = "Set Meshparts to Highest LOD",
        description = "Overwrites all meshparts' explicit LODs to the highest LOD.",
        default = True)
    coerce_fourth = BoolProperty(
        name = "Coerce 4th Negative Weight",
        description = "Forces non-explicit 4 weight vertices into a 4 weight blocktype.",
        default = True)

class mhwSetOfSetsObj(PropertyGroup):
    name=StringProperty()
    export=BoolProperty(default=1)
    #obje=PointerProperty(type=mhwExpSet)
    #obje=PointerProperty(type=bpy.types.Object)
    #obje=PointerProperty(type=mhwExpSet)
class mhwSetOfSets(PropertyGroup):
    name=StringProperty()
    oindex=IntProperty()
    eobjs=CollectionProperty(type=mhwSetOfSetsObj)
    sets_path=StringProperty(subtype='FILE_PATH')
    use_sets_path=BoolProperty(default=1,description='Use this path for each set' )
    exMod3=BoolProperty(default=1)
    exCTC=BoolProperty()
    exCCL=BoolProperty()
    nativePCappend=BoolProperty()
    perSetCustomPathUse=BoolProperty()
class mhwArmorNum(PropertyGroup):
    name=StringProperty()
    num=StringProperty()
class dpMHW_help(PropertyGroup):
    gamepath=StringProperty(subtype='FILE_PATH',description='Example : C:/Program Files (x86)/Steam/steamapps/common/Monster Hunter World/')
    resource_path=StringProperty(subtype='FILE_PATH')
    oindex=IntProperty()
    oindex2=IntProperty()
    saveable=['gamepath','resource_path']
    per_scene=[]
    export_set=CollectionProperty(type=mhwExpSet)
    export_setofsets=CollectionProperty(type=mhwSetOfSets)
    armor_num=CollectionProperty(type=mhwArmorNum)
    
    show_options=BoolProperty()
    show_setofsets=BoolProperty(default=0)
    show_main_sets=BoolProperty(default=1)
def SaveSettings(context):
    
    scene=context.scene
    blen=bpy.path.basename(bpy.context.blend_data.filepath)
    savedump={blen:{}}
    sd=savedump[blen]
    for _scene in bpy.data.scenes:
        mhw=_scene.mhwsake
        sd[_scene.name]={}
        for i in mhw.per_scene:
            sd[_scene.name][i]=getattr(mhw,i)
    savedump['Global Settings']={'gamepath':scene.mhwsake.gamepath}
    if os.path.exists(json_savepath):
        with open(json_savepath,'r') as jsav:to_upd=json.load(jsav)
            
        to_upd.update(savedump)
        savedump=to_upd
    with open(json_savepath,'w') as jsav:json.dump(savedump,jsav, indent=1, sort_keys=True)
def ApplySettingsToScenes(var,context):
    scene=context.scene
    mhw=bpy.context.scene.mhwsake
    var_val=getattr(mhw,var)
    for scene in bpy.data.scenes:
        mhw=scene.mhwsake
        setattr(mhw,var,var_val)
def goto_set_dir(context):
    scene=context.scene
    mhw=scene.mhwsake
    _set=mhw.export_set[mhw.oindex]
    
    os.startfile(path)
    #todo, button that opens a directory of chosen set
def MHW_Export(context,expwhat='Mod3',gamepath=None,nativePCappend=True,allow_custom_path=True,is_batch=False):
    scene=context.scene
    
    mhw=scene.mhwsake
    _set=mhw.export_set[mhw.oindex]
    obsave={}
    obs=scene.objects
    
    if expwhat!='CTC':
        #bpy.ops.mod_tools.target_weights()
        #scene.update()
        layersave=[a for a in scene.layers]
        valid_obs=[a.obje for a in _set.eobjs if a.export==1 and scene.objects.get(a.name)!=None]
        if expwhat=='CCL':
            valid_obs=[a for a in valid_obs if a.get('Type') and a['Type']=='CCL']
    
    if expwhat!='CTC' and valid_obs==[] :
        ShowMessageBox('No objects to export.','Error','MESH_CUBE')
        return
    if mhw.armor_num.get(_set.armor_name)==None:
        ShowMessageBox('Armor set not chosen.','Error','ERROR')
        return

    if expwhat=='Mod3':
        _ext='mod3'
        uni_root=_set.empty_root
        uni_target='SkeletonRoot'
    elif expwhat=='CTC':
        _ext='ctc'
        uni_root=_set.ctc_header
        uni_target='CTC'
    elif expwhat=='CCL':
        _ext='ccl'
        uni_root='None'
        uni_target='CCL'
    #if expwhat=='Mod3':
    type_resets=['CTC','SkeletonRoot','CCL']
    for o in scene.objects:
        
        obsave[o]={'hide':o.hide} #Restoring visibility after export.
        if o.get('Type')!=None and o['Type'] in type_resets:
            obsave[o]['Type']=o['Type']
            o['Type']='aaaa'
        if o==uni_root or (expwhat=='CCL' and o in valid_obs):
            o['Type']=uni_target
            print('Root/Ctc %s'%uni_root.name)
        if expwhat!='Mod3':continue
        
        if o not in valid_obs:
            o.hide=1
            continue
        else:o.hide=0
            
        oblayers=[l for l in o.layers]
        for n,(ol,ll) in enumerate(zip(oblayers,layersave)):
            if ol==True and ll==False:
                scene.layers[n]=True
                break
    
    if gamepath==None:gamepath=mhw.gamepath
    armorname=mhw.armor_num[_set.armor_name].num
    if _set.nativePCappend:nativePCappend=True
    gender=_set.gender
    if nativePCappend:
        path_template='{gamepath}nativePC\\pl\\{gender}_equip\\{armorname}\\{armor_part}\\mod\\{gender}_{armor_part}{armorname2}.{ext}'
    else:
        path_template='{gamepath}\\{gender}_{armor_part}{armorname2}.{ext}'
    
    if  _set.use_custom_path and len(_set.custom_export_path)>3 and allow_custom_path:
        if nativePCappend and is_batch:
            cappend2='\\nativePC\\pl\\{gender}_equip\\{armorname}\\{armor_part}\\mod\\'
        else:cappend2=''
        expath=set.custom_export_path+cappend2+'\\{gender}_{armor_part}{armorname2}.{ext}'.format(
        gender=gender,
        armor_part=_set.armor_part,
        armorname2=  armorname[2:],
        ext=_ext
        )
        
    else:
        expath=path_template.format(
        gamepath=gamepath,gender=gender,
        armor_part=_set.armor_part,
        armorname= armorname,
        armorname2=  armorname[2:],
        ext=_ext
        )
    raw_expath=expath.replace(expath.split('\\')[-1],'')
    if not os.path.exists(raw_expath):
        try:
            os.makedirs(raw_expath)
            print('Created a directory:\n',raw_expath)
        except:
            pass
    scene.update()
    if os.path.exists(raw_expath):
        if expwhat=='Mod3':
            #print('MHW Organizer roots print:\n',list(a.name for a in obs if a.get('Type') and a['Type']=='SkeletonRoot'))
            bpy.ops.custom_export.export_mhw_mod3(filepath=expath,export_hidden=False,
            coerce_fourth=_set.coerce_fourth,split_normals=_set.split_normals,highest_lod=_set.highest_lod)
        elif expwhat=='CTC':
            bpy.ops.custom_export.export_mhw_ctc(filepath=expath)
        elif expwhat=='CCL':
            bpy.ops.custom_export.export_mhw_ccl(filepath=expath)

    else:print('Could not find path to save to',raw_expath)

    for o in obsave:#in scene.objects:
        o.hide=obsave[o]['hide']
        if obsave[o].get('Type'):o['Type']=obsave[o]['Type']
    
    if expwhat=='Mod3':
        for n,l in enumerate(layersave):scene.layers[n]=l
        #bpy.ops.mod_tools.target_armature()
    print('-Succesfully Exported %s:\n'%expwhat,expath)
def find_col_index(name,collection):
    for i,st in enumerate(collection):
        if st.name==name:
            return i
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
 }
def BatchSetsExport(context):
    scn=context.scene
    mhw=scn.mhwsake
    idx = mhw.oindex2
    mainsets=mhw.export_set
    _set=mhw.export_setofsets[idx]
    ex_path=_set.sets_path if len(_set.sets_path)>2 and _set.use_sets_path else None
    native_append=_set.nativePCappend
    allow_custom_path=_set.perSetCustomPathUse
    for sse in _set.eobjs:
        
        if mainsets.get(sse.name)!=None and sse.export==1:
            
            ind=find_col_index(sse.name,mainsets)
            if ind==None:
                print('Something went wrong choosing the %s set'%sse.name)
                continue

            mhw.oindex=ind
            context.scene.update()
            #print(sse.name,_set.exMod3,mhw.oindex)
            for if_export,expwhat in [[_set.exMod3,'Mod3'],[_set.exCTC,'CTC'],[_set.exCCL,'CCL']]:
                if if_export:
                    MHW_Export(context,expwhat=expwhat,
                    gamepath=ex_path,
                    nativePCappend=native_append,
                    allow_custom_path=allow_custom_path,
                    is_batch=True)

            # if _set.exMod3:
                
                # MHW_Export(context,expwhat='Mod3',gamepath=ex_path,nativePCappend=native_append,allow_custom_path=allow_custom_path)
            # if _set.exCTC:
                # MHW_Export(context,expwhat='CTC',gamepath=ex_path,nativePCappend=native_append,allow_custom_path=allow_custom_path)
            # if _set.exCCL:
                # MHW_Export(context,expwhat='CCL',gamepath=ex_path,nativePCappend=native_append,allow_custom_path=allow_custom_path)
        else:print('Something went wrong choosing the %s set'%sse.name)
class dpmhwButton(bpy.types.Operator):
    bl_idname = "scene.dpmhw_button"
    bl_label = "Bool"
    name=bpy.props.StringProperty()
    func=bpy.props.StringProperty()
    var1=bpy.props.StringProperty()
    def execute(self,context):
        scene=context.scene
        #wiz=scene.Bwiz
        if self.func=='Save Settings':
            SaveSettings(context)
        elif self.func=='ApplySettingsToScenes':
            ApplySettingsToScenes(self.name,context)
        elif self.func=='MHW_Export':
            MHW_Export(context)
        elif self.func=='MHW_Export_CTC':
            MHW_Export(context,'CTC')
        elif self.func=='MHW_Export_CCL':
            MHW_Export(context,'CCL')
        elif self.func=='refresh_armor_numbers':
            refresh_armor_numbers()
        elif self.func=='reload_settings':
            reload_settings()
        elif self.func=='goto_set_dir': #not implemented yet, go to directory
            goto_set_dir(context)
        elif self.func=='show_info':
            ShowMessageBox(infos[self.var1],'Info','MESH_CUBE')
        elif self.func=='BatchSetsExport':
            BatchSetsExport(context)
            #show_info(context,self.var1)
        return {'FINISHED'}

def ico(name):
       #global custom_icons
       return custom_icons.get(name).icon_id
class dpMHW_panel(bpy.types.Panel):
    """Creates a Panel in the Tool Shelf"""
    bl_label = "MOD3 Export Set Organizer"
    bl_idname = "MOD3 Export Set Organizer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "MHW Tools"

    def draw(self,context):
        global custom_icons
        context = bpy.context
        scene=context.scene
        mhw=bpy.context.scene.mhwsake
        layout=self.layout
        row=layout.row()
        sbox=row.box()
        row=sbox.row()
        row.prop(mhw,'gamepath',text='Game')
        # gp=row.operator('scene.dpmhw_button',text='[+]')
        # gp.func='ApplySettingsToScenes'
        # gp.name='gamepath'
        row=sbox.row()
        row.operator('scene.dpmhw_button',text='Save Settings',icon='GREASEPENCIL').func='Save Settings'
        row=sbox.row()
        row.label('Reload all scenes:',icon='SCENE_DATA')
        help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
        help1.var1,help1.func='scenes_reload','show_info'
        row=sbox.row()
        row.operator('scene.dpmhw_button',text='Settings',icon='FILE_SCRIPT').func='reload_settings'
        row.operator('scene.dpmhw_button',text='Armor Numbers',icon='LINENUMBERS_ON').func='refresh_armor_numbers'
        row=sbox.row()
        row=layout.row()
        sbox=row.box()
        row=sbox.row(align=1)
        row.label('Sets of Sets:')
        row.prop(mhw,'show_setofsets',text='Toggle View',icon='NLA')
        if mhw.show_setofsets:
            
            if mhw.oindex2<=len(mhw.export_setofsets) and len(mhw.export_setofsets)>0:
                _set=mhw.export_setofsets[mhw.oindex2]
                row=sbox.row(align=1)
                row.prop(_set,'sets_path',text='Exportpath')
                row.prop(_set,'use_sets_path',text='',icon=['RADIOBUT_OFF','RADIOBUT_ON'][_set.use_sets_path])
                row=sbox.row(align=1)
                help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
                help1.var1,help1.func='append_native','show_info'
                row.prop(_set,'nativePCappend',text='Append: \\nativePC\\.. etc..',icon='WORDWRAP_OFF')
                row.prop(_set,'perSetCustomPathUse',text='UsePerSetCustomPath',icon='SYNTAX_OFF')
                row=sbox.row(align=1)
                row.prop(_set,'exMod3',icon_value=ico('export'))
                row.prop(_set,'exCTC',icon='MOD_SIMPLEDEFORM')
                row.prop(_set,'exCCL',icon='META_CAPSULE')
                row=sbox.row(align=1)
                row.operator('scene.dpmhw_button',text='Batch Export: %s'%_set.name,icon='STRANDS').func='BatchSetsExport'
            row=sbox.row(align=1)
            col = row.column(align=True)
            rows=2
            #row=sbox.row()
            
            row.template_list("dpMHW_drawSetOfSets", "", mhw, "export_setofsets", mhw, "oindex2", rows=rows)
            
            col.operator("scene.dpmhw_setofsets_arranger", icon='ZOOMIN', text="").action = 'ADD'
            col.operator("scene.dpmhw_setofsets_arranger", icon='ZOOMOUT', text="").action = 'REMOVE'
            col.separator()
            col.operator("scene.dpmhw_setofsets_arranger", icon='TRIA_UP', text="").action = 'UP'
            col.operator("scene.dpmhw_setofsets_arranger", icon='TRIA_DOWN', text="").action = 'DOWN'
            if mhw.oindex2<=len(mhw.export_setofsets) and len(mhw.export_setofsets)>0:#and len(mhw.export_set[mhw.oindex].eobjs)>0:
                _set=mhw.export_setofsets[mhw.oindex2]
                row=sbox.row(align=1)
                
                row.label(text="Set of Sets's Objects:",icon='MESH_CUBE')
                # help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
                # help1.var1,help1.func='obj_info','show_info'
                row=sbox.row()
                col = row.column(align=True)
                
                row.template_list("dpMHW_drawSetOfSetsObjs", "", _set, "eobjs", _set, "oindex", rows=rows)
                
                col.operator("scene.dpmhw_setofsets_obj_arranger", icon='ZOOMIN', text="").action = 'ADD'
                col.operator("scene.dpmhw_setofsets_obj_arranger", icon='ZOOMOUT', text="").action = 'REMOVE'
                col.separator()
                col.operator("scene.dpmhw_setofsets_obj_arranger", icon='TRIA_UP', text="").action = 'UP'
                col.operator("scene.dpmhw_setofsets_obj_arranger", icon='TRIA_DOWN', text="").action = 'DOWN'
        
        row=layout.row()
        sbox=row.box()
        row=sbox.row(align=1)
        row.label(text='Main sets:')
        row.prop(mhw,'show_main_sets',text='Toggle View',icon='NLA')
        row=sbox.row(align=1)
        if mhw.show_main_sets:
            if mhw.oindex<=len(mhw.export_set) and len(mhw.export_set)>0:
                _set=mhw.export_set[mhw.oindex]
                aktset='%s'%mhw.export_set[mhw.oindex].name
                if mhw.armor_num.get(_set.armor_name):
                    armorname=mhw.armor_num[_set.armor_name].num
                    aktset+=' (%s)'%armorname
                row=sbox.row()
                row.label('%s, export:'%aktset,icon='ZOOM_SELECTED')
                row=sbox.row(align=1)
                row.operator('scene.dpmhw_button',text='MOD3',icon_value=ico('export')).func='MHW_Export'
                row.operator('scene.dpmhw_button',text='CTC',icon='MOD_SIMPLEDEFORM').func='MHW_Export_CTC'
                row.operator('scene.dpmhw_button',text='CCL',icon='META_CAPSULE').func='MHW_Export_CCL'

                
                row2=sbox.row(align=1)
                row2.label('Active Set Settings:',icon='FILE_TEXT')
                row2=sbox.row(align=1)
                row2.prop_search(_set,'armor_name',mhw,'armor_num',text='')
                row2.prop(_set,'armor_part',text='',icon_value=ico(_set.armor_part),expand=0)
                row2.prop(_set,'gender',text='',expand=0)
                row2=sbox.row(align=1)
                row2.prop(_set,'empty_root',text='Root',icon='OUTLINER_OB_MESH')
                row2=sbox.row(align=1)
                row2.prop(_set,'ctc_header',text='CTC_header',icon='OUTLINER_OB_FORCE_FIELD')
                row2=sbox.row(align=1)
                
                
                row2.prop(_set,'custom_export_path',text='Custom Export Path')
                row2.prop(_set,'nativePCappend',text='nativeAppend',icon='WORDWRAP_OFF')
                row2=sbox.row(align=1)
                row2.prop(_set,'use_custom_path',text='Use Custom Export Path',icon='COPY_ID')
                row2=sbox.row(align=1)
                row2.prop(mhw,'show_options',text='Toggle more Options',icon_value=ico('show_options'))
                if mhw.show_options:
                    row=sbox.row()
                    box2=row.box()
                    row=box2.row()
                    row.label('Per set options:')
                    row=box2.row()
                    row.prop(_set,'split_normals')
                    row=box2.row()
                    row.prop(_set,'highest_lod')
                    row=box2.row()
                    row.prop(_set,'coerce_fourth')
            row=sbox.row()
            row.label(text='Choose/Add Active Set:',icon='COLLAPSEMENU')
            row=sbox.row()
            col = row.column(align=True)
            rows=2
            row.template_list("dpMHW_drawSet", "", mhw, "export_set", mhw, "oindex", rows=rows)
            
            col.operator("scene.dpmhw_set_arranger", icon='ZOOMIN', text="").action = 'ADD'
            col.operator("scene.dpmhw_set_arranger", icon='ZOOMOUT', text="").action = 'REMOVE'
            col.separator()
            col.operator("scene.dpmhw_set_arranger", icon='TRIA_UP', text="").action = 'UP'
            col.operator("scene.dpmhw_set_arranger", icon='TRIA_DOWN', text="").action = 'DOWN'
            if mhw.oindex<=len(mhw.export_set) and len(mhw.export_set)>0:#and len(mhw.export_set[mhw.oindex].eobjs)>0:
                _set=mhw.export_set[mhw.oindex]
                row=sbox.row(align=1)
                
                row.label(text="Set's Objects:",icon='MESH_CUBE')
                row.operator("scene.dpmhw_obj_arranger", icon='ROTATE', text="Add All Selected").action = 'BATCHADD'
                help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
                help1.var1,help1.func='obj_info','show_info'
                row=sbox.row()
                col = row.column(align=True)
                
                row.template_list("dpMHW_drawObjSet", "", _set, "eobjs", _set, "oindex", rows=rows)
                
                col.operator("scene.dpmhw_obj_arranger", icon='ZOOMIN', text="").action = 'ADD'
                col.operator("scene.dpmhw_obj_arranger", icon='ZOOMOUT', text="").action = 'REMOVE'
                col.separator()
                col.operator("scene.dpmhw_obj_arranger", icon='TRIA_UP', text="").action = 'UP'
                col.operator("scene.dpmhw_obj_arranger", icon='TRIA_DOWN', text="").action = 'DOWN'

def refresh_armor_numbers():
    with open(base_dir+'\\clothes_num.json','r') as jsr:dict=json.load(jsr)
    for scene in bpy.data.scenes:
        mhw=scene.mhwsake
        while len(mhw.armor_num)>0:mhw.armor_num.remove(0)
        for i in dict:
            add=mhw.armor_num.add()
            add.name=i
            add.num=dict[i]
def reload_settings():
    if os.path.exists(json_savepath):
       with open(json_savepath,'r') as rp:jsr=json.load(rp)
            
       for scene in bpy.data.scenes:
            mhw=scene.mhwsake
            mhw.gamepath=jsr['Global Settings']['gamepath']

@persistent
def post_load(scene):

    context = bpy.context
    scene=context.scene
    mhw=scene.mhwsake

    refresh_armor_numbers()
    reload_settings()
    #print("WTF")
    #This handler function is ran twice, not sure why,
    #can see it 'WTF' is printed twice.

       
bpy.app.handlers.load_post.append(post_load)

def register():
    #if post_load in bpy.app.handlers.load_post: return
    global custom_icons

    bpy.utils.register_module(__name__)
    bpy.types.Scene.mhwsake = PointerProperty(type=dpMHW_help)
    bpy.types.Scene.mhwsetsz=PointerProperty(type=mhwExpSet)
    custom_icons = bpy.utils.previews.new()
    for i in glob.glob(base_dir+'/icons/*.png'):
        custom_icons.load(i.split('\\')[-1][:-4] , i, 'IMAGE')
def unregister():
    global custom_icons
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.mhwsake
    del bpy.types.Scene.mhwsetsz
    
    for i in custom_icons.values():bpy.utils.previews.remove(i)
    custom_icons.clear()
if __name__ == "mhw_set_organizer":
    register()