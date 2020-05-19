

import bpy,os,sys,json,glob,importlib
from bpy.app.handlers import persistent


base_dir = os.path.dirname(os.path.realpath(__file__))
if not base_dir in sys.path:sys.path.append(base_dir)
#
from general_functions import *
from gui_stuff.dpmhw_arrangers import *
from operators.usual_operators import *


from re import findall
from bpy.props import EnumProperty,StringProperty,BoolProperty,FloatProperty,IntProperty,CollectionProperty,PointerProperty
from bpy.types import PropertyGroup,Operator
from mathutils import Matrix

json_savepath=base_dir+'\\MhwSettings.json'

armor_parts_enum=['leg','wst','arm','body','helm']

def ico(name):
       #global custom_icons
       return custom_icons.get(name).icon_id
class ob_copy_VG(PropertyGroup):
    name=StringProperty()
    
    obje=PointerProperty(type=bpy.types.Object)
    #vg=PointerProperty(type=bpy.types.VertexGroup)
    
class mhwExpSetObj(PropertyGroup):
    name=StringProperty()
    export=BoolProperty(default=1)
    obje=PointerProperty(type=bpy.types.Object)
    to_copy=BoolProperty()
    tag=StringProperty()
    preserve_quad=BoolProperty(description='Make a copy of mesh on export and triangulate it, preserving original mesh')
    apply_shape_keys=BoolProperty()

class ob_copy_track(PropertyGroup):
    name=StringProperty() #not needed, pretty sure
    caster=PointerProperty(type=bpy.types.Object)
    ctc_src=PointerProperty(type=bpy.types.Object)
    armature=PointerProperty(type=bpy.types.Object)
    o2=PointerProperty(type=bpy.types.Object)
    edit_view=BoolProperty(default=0)
    ttype=StringProperty()
    is_new=BoolProperty()
    bone_id=IntProperty(default=0)
    changed_id=IntProperty(default=0)
    VG=CollectionProperty(type=ob_copy_VG)
    id_name=StringProperty()
    #vertex_group=PointerProperty(type=bpy.types.VertexGroup)
class ctc_copy_sources(PropertyGroup):
    name=StringProperty()
    source=PointerProperty(type=bpy.types.Object)
    target=PointerProperty(type=bpy.types.Object)
    copy_src_track=CollectionProperty(type=ob_copy_track)
    show_copied=BoolProperty()
    edit_source=BoolProperty()
    edit_targets=BoolProperty()
    edit_filter=StringProperty()
    
    view_mode_icons={'List View':'LINENUMBERS_OFF','Edit Source':'RNA','Edit Copies':'COPY_ID'}
    view_mode=EnumProperty(items=[(a,a,a) for a in ['List View','Edit Source','Edit Copies']],default='Edit Copies')
    view_toggle=BoolProperty(default=1)
    
    filter_header=BoolProperty(default=1)
    filter_chain=BoolProperty(default=1)
    filter_frame=BoolProperty(default=1)
    filter_bone=BoolProperty(default=1)
    info_when_closed=BoolProperty(description='Show some properties even if tab of object is closed')

native_str='\\nativePC\\pl\\{gender}_equip\\{armorname}\\{armor_part}\\mod\\'
just_file_str='\\{gender}_{armor_part}{armorname2}'

def upd_exp_path(self,context):
    scene=context.scene
    mhw=scene.mhwsake
    batch_custom_path,batch_native_override=None,None
    if mhw.oindex2<=len(mhw.export_setofsets) and len(mhw.export_setofsets)>0:
        _sset=mhw.export_setofsets[mhw.oindex2]
        if self.is_batch:
            batch_custom_path=_sset.sets_path if _sset.use_sets_path==False else None
            batch_native_override=_sset.nativePCappend
    armorname=mhw.armor_num[self.armor_name].num if mhw.armor_num.get(self.armor_name) else '  ChooseArmor'
    native=native_str.format(gender=self.gender,
    armor_part=self.armor_part,
    armorname=armorname,
    )
    native_check = self.nativePCappend if batch_native_override==None else batch_native_override
    cp=self.custom_export_path if batch_custom_path==None else batch_custom_path
    if cp!='' and os.path.exists(cp):
        exp_root=cp
        native_add='' if not native_check else native
    else:
        exp_root=mhw.gamepath
        native_add=native
    native_add=native_add if native not in exp_root else ''
    self.export_path=exp_root+native_add+just_file_str.format(gender=self.gender,armorname2= armorname[2:],armor_part=self.armor_part)

class mhwExpSet(PropertyGroup):
    name=StringProperty()
    oindex=IntProperty()
    eobjs=CollectionProperty(type=mhwExpSetObj)
    nativePCappend=BoolProperty(update=upd_exp_path)
    armor_name=StringProperty(update=upd_exp_path)
    armor_part=EnumProperty(items=[(a,a,a) for a in armor_parts_enum],update=upd_exp_path)
    gender=EnumProperty(items=[(a,a,a) for a in ['f','m']],default='f',update=upd_exp_path)
    empty_root=PointerProperty(type=bpy.types.Object,poll=empty_root_poll)
    custom_export_path=StringProperty(subtype='FILE_PATH',update=upd_exp_path)
    use_custom_path=BoolProperty(update=upd_exp_path)
    more_obj_options=BoolProperty(default=1,name='More Object Options')
    
    ctc_header=PointerProperty(type=bpy.types.Object,poll=header_copy_poll)
    ctc_copy_src=CollectionProperty(type=ctc_copy_sources)
    clean_after_ctc_copy=BoolProperty(default=1,name='Clean Groups')
    normalize_active=BoolProperty(default=1,name='Normalize Groups')
    ctc_copy_weights=BoolProperty(default=1,name='Copy Weights')
    
    show_ctc_manager=BoolProperty()
    export_path=StringProperty()
    is_batch=BoolProperty()
    
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


class blenderAppend(PropertyGroup):
    path=StringProperty(subtype='FILE_PATH')

class ext_ctc_source(PropertyGroup):
    blend=StringProperty()
    folder=StringProperty()
    
class dpMHW_help(PropertyGroup):
    gamepath=StringProperty(subtype='FILE_PATH',description='Example : C:/Program Files (x86)/Steam/steamapps/common/Monster Hunter World/')
    resource_path=StringProperty(subtype='FILE_PATH')
    oindex=IntProperty()
    oindex2=IntProperty()
    oindex_blend=IntProperty()
    saveable=['gamepath','resource_path']
    per_scene=[]
    export_set=CollectionProperty(type=mhwExpSet)
    export_setofsets=CollectionProperty(type=mhwSetOfSets)
    armor_num=CollectionProperty(type=mhwArmorNum)

    show_options=BoolProperty()
    show_setofsets=BoolProperty(default=0)
    show_main_sets=BoolProperty(default=1)
    
    header_copy_source=PointerProperty(name='Header',type=bpy.types.Object,poll=header_copy_poll)
    ext_header_copy_name=StringProperty()
    show_header_copy=BoolProperty(default=0)
    header_copy_name=StringProperty()
    header_new_names=StringProperty()
    ctc_copy_use_active=BoolProperty(description="Use active set's Root or active object")
    ctc_copy_add_LR=BoolProperty(default=1)
    ctc_copy_addVG=BoolProperty(default=1)
    ctc_copy_wgt_src=PointerProperty(name='Weight Transfer Source',type=bpy.types.Object,poll=mesh_poll,description='Optional, object to transfer weights with')
    
    append_dirs=CollectionProperty(type=blenderAppend)
    show_dirs_paths=BoolProperty()
    
    extctc_src=CollectionProperty(type=ext_ctc_source)
    show_resource_list=BoolProperty()
    type_infront=BoolProperty(description='Object time infront or back of name, like "Bone Leg.R"')

def SaveSettings(context):
    
    scene=context.scene
    blen=bpy.path.basename(bpy.context.blend_data.filepath)
    savedump={blen:{}}
    sd=savedump[blen]
    append_paths=[]
    for _scene in bpy.data.scenes:
        mhw=_scene.mhwsake
        sd[_scene.name]={}
        for i in mhw.per_scene:
            sd[_scene.name][i]=getattr(mhw,i)
        for p in mhw.append_dirs:
            if p.path!='' and p.path not in append_paths:append_paths.append(p.path)
                    
    savedump['Global Settings']={'gamepath':scene.mhwsake.gamepath}
    if os.path.exists(json_savepath):
        with open(json_savepath,'r') as jsav:to_upd=json.load(jsav)
        append_paths.extend(to_upd['Global Settings']['BlendAppendPaths'])
        to_upd.update(savedump)
        savedump=to_upd
    append_paths=list(set(append_paths))
    savedump['Global Settings']['BlendAppendPaths']=append_paths
    with open(json_savepath,'w') as jsav:json.dump(savedump,jsav, indent=1, sort_keys=True)

def ApplySettingsToScenes(var,context):
    scene=context.scene
    mhw=bpy.context.scene.mhwsake
    var_val=getattr(mhw,var)
    for scene in bpy.data.scenes:
        mhw=scene.mhwsake
        setattr(mhw,var,var_val)

def MHW_Export(context,expwhat='Mod3',gamepath=None,nativePCappend=True,allow_custom_path=True,is_batch=False):
    scene=context.scene
    mhw=scene.mhwsake
    _set=mhw.export_set[mhw.oindex]
    _set.is_batch=is_batch
    obsave={}
    obs=scene.objects
    import bmesh
    if expwhat!='CTC':
        #bpy.ops.mod_tools.target_weights()
        #scene.update()
        layersave=[a for a in scene.layers]
        valid_obs=[a.obje for a in _set.eobjs if a.export==1 and a.obje!=None]
        if expwhat=='CCL':
            valid_obs=[a for a in valid_obs if a.get('Type') and a['Type']=='CCL']
    
    if expwhat!='CTC' and valid_obs==[] :
        ShowMessageBox('No objects to export.','Error','MESH_CUBE')
        return
    if mhw.armor_num.get(_set.armor_name)==None:
        ShowMessageBox('Armor set not chosen.','Error','ERROR')
        return
    quad_save={}
    if expwhat=='Mod3':
        _ext='.mod3'
        uni_root=_set.empty_root
        uni_target='SkeletonRoot'
        
        for o in [a  for a in _set.eobjs if a.preserve_quad and a.obje in valid_obs]:
            quad_save[o.obje]=o.obje.data
            mesh_tri=o.obje.data.copy()
            bm = bmesh.new()
            bm.from_mesh(mesh_tri)
            bmesh.ops.triangulate(bm, faces=bm.faces)
            bm.to_mesh(mesh_tri)
            bm.free()
            o.obje.data=mesh_tri
            mesh_tri.update(calc_tessface=False)
            scene.update()
    elif expwhat=='CTC':
        _ext='.ctc'
        uni_root=_set.ctc_header
        uni_target='CTC'
    elif expwhat=='CCL':
        _ext='.ccl'
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
    upd_exp_path(_set,context)
    expath=_set.export_path+_ext
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
    for o in quad_save:o.data=quad_save[o]
        
    if expwhat=='Mod3':
        for n,l in enumerate(layersave):scene.layers[n]=l
        #bpy.ops.mod_tools.target_armature()
    print('-Succesfully Exported %s:\n'%expwhat,expath)


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
            _settt=mhw.export_set[mhw.oindex]
            _settt.is_batch=False
            upd_exp_path(_settt,context)
        else:print('Something went wrong choosing the %s set'%sse.name)

class ctcO():
    def __init__(self,**args):
        self.parent=None
        self.con=None
        self.changed_id=None
        for a in args.keys():setattr(self, a, args[a])
        
        ctcO.obs[self.tty][self.o]=self
        if self.o.constraints.get('Bone Function'):
            self.con=self.o.constraints['Bone Function']
    def ex(self,what):
            return True if self.__dict__.get(what)!=None else False
    
    def set_parent(self,parent):
        if not self.ex('parent'):self.parent=parent

def CopyCTC(self,context,copy_from):
    scene=context.scene
    mhw=scene.mhwsake
    _set=mhw.export_set[mhw.oindex]
    found_root=None
    if mhw.ctc_copy_use_active:
        target=scene.active_object if _set.empty_root==None else _set.empty_root
    else:
        target=_set.empty_root if _set.empty_root!=None else scene.active_object
    
    _arma=all_heir(target)
    arma={ob:ob.get('boneFunction') for ob in _arma}
    arma_re={ob.get('boneFunction'):ob for ob in _arma}
    the_set=None
    bone_additional=[]
    if target==context.active_object:
        for i in mhw.export_set:
            if i.empty_root==target:the_set=i
    else:
        the_set=_set
    header_tar=_set.ctc_header if _set.ctc_header!=None else None

    if copy_from=='Local':
        source=mhw.header_copy_source
        src_heir=all_heir(source)
    else:
        src=mhw.ext_header_copy_name
        blendf,src_real=src.split('.blend__')
        portscene='ext_%s'%blendf
        srcol=mhw.extctc_src[src]
        
        if bpy.data.objects.get(src)==None: #TODO, add toggle to reload-refresh
            with bpy.data.libraries.load(srcol.blend, link=True) as (data_from, data_to):
                data_to.objects = [name for name in data_from.objects]
        heade=None
        for ob in data_to.objects:
            if ob.name==src_real:
                heade=ob
                break
            #if ob.name=='f_leg074_0000 Armature':print("WTF!")
        if heade==None:return
        if bpy.data.scenes.get(portscene)==None:scene=bpy.data.scenes.new(name=portscene)
        else:scene=bpy.data.scenes[portscene]
        sob=scene.objects
        #scene.objects.link(heade)
        
        src_heir=all_heir(heade)
        source=scene.objects[heade.name]
    source_bone_hie={}
    for h in src_heir:
        if  h.constraints.get('Bone Function')!=None and h.constraints['Bone Function'].target!=None:
            proot=h.constraints['Bone Function'].target
            hier=[]
            bone_additional.append(proot)
            while proot!=None:
                if proot.get('boneFunction'):
                    source_bone_hie[proot['boneFunction']]=proot.parent['boneFunction'] if proot.parent!=None and proot.parent.get('boneFunction') else 0
                proot=proot.parent
                bone_additional.append(proot)
                hier.append(proot)
                #if proot==None:continue #or proot.parent==None:continue
                #if proot.get('boneFunction')==None:continue
            if len(hier)<3:continue
            if found_root==None:
                found_root=hier[-2]
                src_bone_hier=all_heir(found_root)

    if copy_from!='Local':
        for h in bone_additional+src_heir:
            try:
                sob.link(h)
            except:
                pass
    if target==None or source==None:
        self.report({'ERROR'},'Missing; Source: %s, Target %s'%(str(source),str(target)))
        return
    bone_additional=list(set([a for a in bone_additional if a!=None and  a.get('boneFunction')]))
    source_set=None
    tag_dict=get_tags(_set,where='Target')

    for s in bpy.data.scenes:
        for se in s.mhwsake.export_set:
            if se.ctc_header==source and source!=None:
                source_set=se
                tag_dict=get_tags(se,tag_dict,where='Source')
                break
    scene.update()
    scene=context.scene
    
    if not any(s.source==source for s in _set.ctc_copy_src):
        ctc_col=_set.ctc_copy_src.add()
        ctc_col.name=source.name
        ctc_col.source=source
        ctc_col.target=target
    else:
        for i in _set.ctc_copy_src:
            if i.source==source:
                ctc_col=i
    
    _src=all_heir(source)
    
    fmax=max(list(arma[a] for a in arma if arma[a]!=None))+1
    ctctrack={}
    
    text_prep,text_new=mhw.header_copy_name,mhw.header_new_names
    _obs=bpy.data.objects
    count_types={'Bone':1,'Header':1,'Frame':1,'Chain':1,'Node':1}
    ctcO.obs={'Bone':{},'Header':{},'Frame':{},'Chain':{},'Node':{}}
    
    total_list=bone_additional+_src
    
    for isr,o in enumerate(_src ):
        if o.get('Type') and o['Type']=='CTC_Node':
            pco=[a for a in o.constraints if a.type=='CHILD_OF']
            if pco==[]:
                continue
            else:pco=pco[0]
            if pco.target==None:continue
            nodebone=pco.target
            total_list.insert(0,nodebone)
            if nodebone.parent!=None and nodebone.parent not in total_list:total_list.insert(0,nodebone.parent)
            
            max_id2=nodebone['boneFunction']
        if header_tar==None and o.get('Type') and o['Type']=='CTC':
            header_tar=o
    
    order=total_list[:]
    total_list=sorted(list(set(total_list)),key=lambda x:order.index(x))
    #remove doubles,preserve sort order, crucial else parenting is messed, is a current flaw ^
    b_ids,changed_ids={},{}
    if max_id2>fmax:fmax=max_id2+1
    elif max_id2==fmax:fmax=fmax+1
    for xx in _set.ctc_copy_src:
        if xx.target!=target:continue
        for a in xx.copy_src_track:
            if a.ttype!='Bone' or a.bone_id==0:continue
            b_ids[a.bone_id]=a
            if a.changed_id!=0:changed_ids[a.changed_id]=a
    #parenting={changed_ids[z] if changed_ids.get(z) else b_ids[z] for z in 
    #arma_re[0]=_set.empty_root
    for isr,o in enumerate(total_list):
        if o==None:continue
        if o.get('Type') and regular_ctc_names.get(o['Type']):tty=regular_ctc_names[o['Type']]
        else:tty='Bone'
        if header_tar!=None and header_tar!=o and tty=='Header':
            _o2=ctcO(tty=tty,o=o,o2=header_tar)
            ctctrack[o]=_o2
            o2track=ob_in_track(ctc_col,o,armature=target,report=self)
            if o2track==None:ob_in_track(ctc_col,o,source,target,header_tar)
            continue
        
        if text_new=='':
            obn='%s%s'%(text_prep,o.name)
            
        else:
            obn='%s%s'%(text_new,count_types[tty] if tty!='Header' else '')
            count_types[tty]+=1
        if tty not in o.name:obn='%s_%s'%(tty,obn) if mhw.type_infront else '%s_%s'%(obn,tty)
        new,o2=0,None
        o_id=o.get('boneFunction')
        
        o2track=ob_in_track(ctc_col,o,armature=target,report=self)
        bone_already=0
        if tty=='Bone':
            if source_bone_hie.get(o_id)==None:
                continue
            pid=source_bone_hie[o_id]
            if b_ids.get(o_id):
                o2track=b_ids[o_id]
                o2=o2track.o2
                bone_already=1
            elif arma_re.get(o_id):
                o2=arma_re[o_id]
                o2track=ob_in_track(ctc_col,o,source,target,o2)
                bone_already=1

        if bone_already==0:
                if o2track!=None:# here we check if object was copied in other sessions, if so, new one is not made
                    o2=o2track.o2
                else:
                    new=1
                    rem_num=findall(r'\.[0-9]*',obn)
                    if rem_num:obn=obn.replace(rem_num[0],'')
                    if _obs.get(obn):
                        nnum=1
                        while _obs.get(obn+'.%03d'%nnum):
                            nnum+=1
                        obn=obn+'.%03d'%nnum
                    o2=new_ob(obn)
                    o2track=ob_in_track(ctc_col,o,source,target,o2)
        o2track.is_new=new
        _o2=ctcO(tty=tty,o=o,o2=o2,bid=o_id)
        ctctrack[o]=_o2
        if o_id!=None:o2track.bone_id=o_id
        b_ids[o_id]=o2track
        if o_id==13:continue
        if 1+1==2:
            if tty=='Bone':
                o2track.id_name='boneFunction'
                if o_id >= 150 and arma_re.get(o_id)!=None and o2track.is_new==1:
                    #shift the boneFunction,but only if it was not before
                    
                    if o2track.changed_id==0:#check if was shifted in previous sessions
                        o_id=fmax
                        o2track.changed_id=fmax
                        self.report({'INFO'},'Shifted boneFunction %s to %s (%s)'%(o['boneFunction'],o_id,o2.name))
                        fmax+=1
                        
                    else:
                        o_id=o2track.changed_id
                
                if changed_ids.get(pid):
                    _o2.set_parent(changed_ids[pid].o2)
                elif b_ids.get(pid):_o2.set_parent(b_ids[pid].o2)
                elif arma_re.get(o_id):
                    _o2.set_parent(arma_re[o_id])

            if ctctrack.get(o.parent):
                _o2.set_parent(ctctrack[o.parent].o2)
            try:
                if _o2.parent!=None:
                    o2.parent=_o2.parent
            except:
                pass
            copy_various_props(o,o2)
            if tty=='Bone':
                o2.parent=None
                o2.matrix_world=o.matrix_world.copy()
                o2['boneFunction']=o2track.changed_id if o2track.changed_id!=0 else o2track.bone_id #overwrite copied Bone props in case boneFunction was shifted
                ntrack=o2.name
            if mhw.ctc_copy_add_LR:

                if not any(o2.name.endswith(x) for x in ['.L','.R']):
                    tbone_X=o2.matrix_world.to_translation()[0]
                    
                    o2.name=o2.name.replace('.R','').replace('.L','')
                    if tbone_X<0:o2.name=o2.name+'.R'
                    elif tbone_X>0:o2.name=o2.name+'.L'
                if ntrack!=o2.name and tty=='Bone' and o['boneFunction']<150:
                    for i in [a for a in _set.eobjs if a.obje !=None]:
                        if i.obje.vertex_groups.get(ntrack):i.obje.vertex_groups.remove(group=i.obje.vertex_groups[ntrack])
            scene.update()
            if tty=='Bone':

                if mhw.ctc_copy_addVG and the_set!=None:
                        for ob in [a for a in the_set.eobjs if a.obje!=None]:
                            if ob.obje.vertex_groups.get(o2.name)==None:
                                vg=ob.obje.vertex_groups.new(name=o2.name)
                            else:vg=ob.obje.vertex_groups[o2.name]
                            if not any(oo.obje==ob.obje  for oo in o2track.VG):
                                ovg=o2track.VG.add()
                                ovg.name=vg.name
                                ovg.obje=ob.obje

        if tty=='Frame':
            bbo=b_ids[o['boneFunctionID']]
            o2['boneFunctionID']=bbo.bone_id if bbo.changed_id==0 else bbo.changed_id
            o2track.changed_id=bbo.changed_id
            o2track.id_name='boneFunctionID'
            o2.rotation_euler=o.rotation_euler
    bones=ctcO.obs['Bone']
    nodes=ctcO.obs['Node']
    frames=ctcO.obs['Frame']
    if _set.ctc_header==None:
        _set.ctc_header=list(ctcO.obs['Header'].values())[0].o2
        self.report({'WARNING'},'%s - set header has been set to source copied header.'%_set.ctc_header.name)
    for bo in bones: #Check for missing parenting
        _bo=ctcO.obs['Bone'][bo]
        if _bo.o2==None:
            continue 
        if _bo.o2.parent==None:
            if bo.parent!=None and bones.get(bo.parent):
                pp=bones[bo.parent].o2
                
                if pp!=None:
                    mcopy=_bo.o.matrix_world.copy()
                    _bo.o2.parent=pp
                    _bo.o2.matrix_world=mcopy
    for node in nodes: #Add constraints to Nodes
        _o2=nodes[node].o2
        if _o2==None:continue
        if nodes[node].con==None:
            self.report({'WARNING'},'%s - could not find constraint.'%nodes[node].o.name)
            continue
        orig_tar=nodes[node].con.target
        bonefind=bones.get(orig_tar)
        if bonefind==None:continue
        if _o2.constraints.get('Bone Function')==None:
            cons=_o2.constraints.new(type='CHILD_OF')
            cons.name='Bone Function'
        else:cons=_o2.constraints['Bone Function']
        cons.target=bones[bonefind.o].o2
        cons.inverse_matrix =nodes[node].o.parent.matrix_world.inverted()#.inverted()#Matrix()
        scene.update()
    new_bonedict={x.name:bones[x].o2.name for x in bones}
        
    if _set.ctc_copy_weights:
        for ttag in tag_dict:
            tag=tag_dict[ttag]
            if tag['Target']==[] or tag['Source']==[]:continue
            modif_state_save,ob_state_save={},{}
            
            for s in tag['Target']+tag['Source']:
                ob_state_save[s]=[s.hide,s.hide_select]
                s.hide=0
                s.hide_select=0
                for m in [a for a in s.modifiers if a.type!='SUBSURF']:
                    modif_state_save[m]=m.show_viewport
                    m.show_viewport=0
            for s in tag['Source']:

                #mco=s.data.copy()
                oco=s.copy()#new_ob(s.name+'_weight_source',mco)
                mcopy=s.data.copy()
                oco.data=mcopy
                scene.objects.link(oco)
                for w in oco.vertex_groups:
                    if new_bonedict.get(w.name):w.name=new_bonedict[w.name]
                    else:oco.vertex_groups.remove(group=w)
                for t in tag['Target']:
                    bpy.ops.object.select_all(action='DESELECT')
                    t.select=1
                    scene.objects.active=t
                    scene.update()
                    
                    mname='%s%s'%(s.name,t.name)
                    if t.modifiers.get(mname)==None:
                        mm = t.modifiers.new(mname, type='DATA_TRANSFER')
                    else:mm=t.modifiers[mname]
                    mm.use_vert_data=True
                    mm.data_types_verts={'VGROUP_WEIGHTS'}
                    mm.vert_mapping="POLYINTERP_NEAREST"
                    mm.object=oco
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.datalayout_transfer(modifier=mname)
                    try:
                        bpy.ops.object.modifier_apply(apply_as='DATA',modifier=mname)
                    except:
                        self.report({'ERROR'},'Could not apply modifier %s on %s, probably a linked object.'%(mname,t.name))
                    if _set.normalize_active:
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        for vg in new_bonedict:
                            vgn=new_bonedict[vg]
                            if t.vertex_groups.get(vgn):
                                t.vertex_groups.active_index=t.vertex_groups.find(vgn)
                                bpy.ops.object.vertex_group_normalize_all(lock_active=True)
                        bpy.ops.object.mode_set(mode='OBJECT')
                bpy.data.objects.remove(oco)
                bpy.data.meshes.remove(mcopy)
            if _set.clean_after_ctc_copy:
                for o in [a for a in _set.eobjs if a.obje !=None]:
                    bpy.ops.object.select_all(action='DESELECT')
                    o.obje.select=1
                    scene.objects.active=o.obje
                    remove_unused_vg(o.obje)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    #bpy.ops.object.vertex_group_limit_total()
                    ldata=o.obje.data['blockLabel']
                    limit=int(findall(r'(?<=IASkin).(?=wt)',ldata)[0])
                    #IASkin8wt1UV
                    bpy.ops.object.vertex_group_limit_total(limit=limit)

                    bpy.ops.object.vertex_group_clean(group_select_mode='ALL')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    
            for m in modif_state_save:m.show_viewport=modif_state_save[m]
            for i in ob_state_save:i.hide,i.hide_select=ob_state_save[i]

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
        _set=mhw.export_set[mhw.oindex] if mhw.oindex<=len(mhw.export_set) and len(mhw.export_set)>0 else False

        row=sbox.row()
        savese=row.operator('scene.dpmhw_button',text='Save Settings',icon='GREASEPENCIL')
        savese.confirmer,savese.func=1,'Save Settings'
        row=sbox.row()
        row.label('Reload all scenes:',icon='SCENE_DATA')
        help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
        help1.var1,help1.func='scenes_reload','show_info'
        row=sbox.row()
        row.operator('scene.dpmhw_button',text='Settings',icon='FILE_SCRIPT').func='reload_settings'
        arm_ic,arm_text=('FILE_TICK','') if len(mhw.armor_num)>0 else ('FILE_REFRESH','(refresh!)')
        row.operator('scene.dpmhw_button',text='Armor Numbers %s'%arm_text,icon=arm_ic).func='refresh_armor_numbers'
        row=sbox.row()
        row.prop(mhw,'show_dirs_paths',text='Blend Append Options')
        if mhw.show_dirs_paths:
            box=sbox.box()
            row=box.row()
            col = row.column(align=True)
            
            row.template_list("dpMHW_drawBlenderAppend", "", mhw, "append_dirs", mhw, "oindex_blend", rows=2)
            
            col.operator("scene.dpmhw_blender_append_arranger", icon='ZOOMIN', text="").action = 'ADD'
            col.operator("scene.dpmhw_blender_append_arranger", icon='ZOOMOUT', text="").action = 'REMOVE'
            col.separator()
            col.operator("scene.dpmhw_blender_append_arranger", icon='TRIA_UP', text="").action = 'UP'
            col.operator("scene.dpmhw_blender_append_arranger", icon='TRIA_DOWN', text="").action = 'DOWN'
            row=box.row()
            row.operator('scene.dpmhw_button',text='Refresh External Sources',icon='FILE_REFRESH').func='reload_external_ctc'
            row.prop(mhw,'show_resource_list',text='List all Resources')
            row=box.row()
            if len(mhw.extctc_src)>0 and mhw.show_resource_list:
                for ex in mhw.extctc_src:
                    row=box.row()
                    row.label(ex.folder+ex.blend,icon='FILE_FOLDER')
                    row.label(ex.name.split('__')[1])
        row=sbox.row()
        row=layout.row()
        sbox=row.box()
        row=sbox.row(align=1)
        row.label('CTC Header Copier:')
        row.prop(mhw,'show_header_copy',text='Toggle View',icon='NLA')
        if mhw.show_header_copy:
            row=sbox.row(align=1)
            row.prop_search(mhw,'header_copy_source',bpy.data,'objects',text='')

            ctcopy=row.operator('scene.dpmhw_button',text='Local Copy',icon='COPYDOWN')
            ctcopy.func,ctcopy.var1='CopyCTC','Local'
            #if len(mhw.extctc_src)>0:
            row=sbox.row(align=1)

            row.operator('scene.dpmhw_button',text='',icon='FILE_REFRESH').func='reload_external_ctc'

            row.prop_search(mhw,'ext_header_copy_name',mhw,'extctc_src',text='',icon='PLUGIN')
            ctcopy=row.operator('scene.dpmhw_button',text='External Copy',icon='APPEND_BLEND')
            ctcopy.func,ctcopy.var1='CopyCTC','External'
            row=sbox.row(align=1)

            row.prop(_set,'ctc_copy_weights',icon='MOD_VERTEX_WEIGHT')
            help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="")
            help1.var1,help1.func='ctc_after_copy','show_info'
            if _set.ctc_copy_weights:
                row=sbox.row()
                row.label('Save before CTC Copy, if toggling on these below!!!')
                row=sbox.row(align=1)
                row.prop(_set,'clean_after_ctc_copy',icon='SNAP_VERTEX')
                row.prop(_set,'normalize_active',icon='SNAP_NORMAL')
            row=sbox.row(align=1)
            row.prop(mhw,'header_copy_name',text='Prepend obj text')
            row.prop(mhw,'header_new_names',text='New Name')
            help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="")
            help1.var1,help1.func='ctc_copy','show_info'
            row=sbox.row(align=1)
            row.prop(mhw,'type_infront',text=['Object Type Name Prefix','Object Name Type Suffix'][mhw.type_infront],icon=['SYNTAX_OFF','SYNTAX_ON'][mhw.type_infront])
            row=sbox.row(align=1)
            row.prop(mhw,'ctc_copy_use_active',text='Target Root: [%s]'%["Active Set's Root",'Active Object'][mhw.ctc_copy_use_active],
            icon=['OUTLINER_DATA_POSE','MESH_CUBE'][mhw.ctc_copy_use_active])
            row=sbox.row(align=1)
            
            row.prop(mhw,'ctc_copy_addVG',text='Add VG per OB',icon='GROUP_VERTEX')
            if mhw.ctc_copy_addVG:
                row.prop(mhw,'ctc_copy_add_LR',text='Add .L/.R to Bones',icon='STICKY_UVS_VERT')
            row=sbox.row(align=1)

        row=layout.row()
        sbox=row.box()
        row=sbox.row(align=1)
        row.label('Sets of Sets:')
        row.prop(mhw,'show_setofsets',text='Toggle View',icon='NLA')
        if mhw.show_setofsets:
            
            if mhw.oindex2<=len(mhw.export_setofsets) and len(mhw.export_setofsets)>0:
                _sset=mhw.export_setofsets[mhw.oindex2]
                row=sbox.row(align=1)
                row.prop(_sset,'sets_path',text='Exportpath')
                row.prop(_sset,'use_sets_path',text='',icon=['RADIOBUT_OFF','RADIOBUT_ON'][_sset.use_sets_path])
                row=sbox.row(align=1)
                help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
                help1.var1,help1.func='append_native','show_info'
                row.prop(_sset,'nativePCappend',text='Append: \\nativePC\\.. etc..',icon='WORDWRAP_OFF')
                row.prop(_sset,'perSetCustomPathUse',text='UsePerSetCustomPath',icon='SYNTAX_OFF')
                row=sbox.row(align=1)
                row.prop(_sset,'exMod3',icon_value=ico('export'))
                row.prop(_sset,'exCTC',icon='MOD_SIMPLEDEFORM')
                row.prop(_sset,'exCCL',icon='META_CAPSULE')
                row=sbox.row(align=1)
                row.operator('scene.dpmhw_button',text='Batch Export: %s'%_sset.name,icon='STRANDS').func='BatchSetsExport'
                row=sbox.row(align=1)

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
            if _set:
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
                row2.prop_search(_set,'empty_root',context.scene,'objects',text='Root',icon='OUTLINER_OB_MESH')
                row2=sbox.row(align=1)
                row2.prop(_set,'ctc_header',text='CTC_header',icon='OUTLINER_OB_FORCE_FIELD')
                row2=sbox.row(align=1)
                
                
                row2.prop(_set,'custom_export_path',text='Custom Export Path')
                row2.prop(_set,'nativePCappend',text='nativeAppend',icon='WORDWRAP_OFF')
                row2=sbox.row(align=1)
                row2.label(_set.export_path)
                if _set.export_path!='':
                    row2.operator('scene.dpmhw_button',text='',icon='FILE_FOLDER').func='goto_set_dir'
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
                row2=sbox.row(align=1)
                row2.prop(_set,'show_ctc_manager',text="Copied CTC's Viewer (WIP)",icon='BOIDS')
                if _set.show_ctc_manager:
                    if len(_set.ctc_copy_src)>0:
                        row=sbox.row()
                        bbo=row.box()
                        row=bbo.row()
                        row.label("%s's usage of copied CTCs:"%_set.name,icon='FORCE_LENNARDJONES')
                        for _i,i in enumerate(_set.ctc_copy_src):
                            bo2=bbo.box()
                            row=bo2.row()
                            row.label('CTC Source: %s'%i.source.name,icon='OUTLINER_OB_META')
                            row.prop(i,'view_toggle',text='Toggle',icon=['PROP_OFF','PROP_ON'][i.view_toggle])
                            if i.view_toggle==0:continue
                            delctc=row.operator('dpmhw.delete_collection',icon='CANCEL',text='')
                            delctc.col_path,delctc.col_num,delctc.del_how='scene.%s'%_set.ctc_copy_src.path_from_id(),_i,'delete_ctc'
                            row=bo2.row()
                            row.prop(i,'view_mode',text='View Mode',icon=i.view_mode_icons[i.view_mode])
                            row=bo2.row(align=1)
                            hall=row.operator('scene.dpmhw_button',text='Un-Expand All',icon='DISCLOSURE_TRI_DOWN')
                            hall.func,hall.var1='ctc_edit_col_edit','{ctcnum}|{setnum}|Hide'.format(ctcnum=_i,setnum=mhw.oindex)
                            hall=row.operator('scene.dpmhw_button',text='Expand All',icon='PLUS')
                            hall.func,hall.var1='ctc_edit_col_edit','{ctcnum}|{setnum}|Show'.format(ctcnum=_i,setnum=mhw.oindex)

                            vupd=row.operator('scene.dpmhw_button',text='Update All Vertex Group Names',icon='SNAP_VERTEX')
                            vupd.func,vupd.var1='batch_refresh_vertex','scene.'+i.path_from_id()

                            row=bo2.row()
                            row=bo2.row(align=1)
                            row.label('Filter:')
                            row.prop(i,'filter_header',text='Header',icon=types_icons['CTC'])
                            row.prop(i,'filter_chain',text='Chain',icon=types_icons['CTC_Chain'])
                            row.prop(i,'filter_frame',text='Frame',icon=types_icons['CTC_*_Frame'])
                            row.prop(i,'filter_bone',text='Bone',icon=types_icons['Bone'])
                            filter_per={'CTC':i.filter_header,'CTC_*_Frame':i.filter_frame,'CTC_Chain':i.filter_chain,'Bone':i.filter_bone}
                            row=bo2.row(align=1)
                            row.prop_search(i,'edit_filter',i,'copy_src_track',text='Pick')
                            hall=row.operator('scene.dpmhw_button',text="Update Internal Names",icon='STYLUS_PRESSURE')
                            hall.func,hall.var1='ctc_edit_col_edit','{ctcnum}|{setnum}|Update'.format(ctcnum=_i,setnum=mhw.oindex)
                            help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
                            help1.var1,help1.func='ctc_edit_update','show_info'
                            row=bo2.row(align=1)
                            row.prop(i,'info_when_closed',icon='WORDWRAP_ON',text='UnexpandedInfo')
                            vupd=row.operator('scene.dpmhw_button',text='Copy Props from Sources',icon='OOPS')
                            vupd.func,vupd.var1,vupd.confirmer='ctc_copy_over_props','scene.'+i.path_from_id(),1
                            help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="") 
                            help1.var1,help1.func='ctc_copy_over_props','show_info'
                            if i.view_mode=='List View': #Not much useful for now, probably can find use in future
                            
                                row=bbo.row()
                                b3=bo2.box()
                                row=b3.row()
                                row.label('Source',icon='EYEDROPPER')
                                row.label('  Target',icon='INLINK')
                                for x in i.copy_src_track:
                                    row=b3.row()
                                    row.label(text="%s"%(x.caster.name ))
                                    row.label(x.o2.name)
                            else:
                                row=bbo.row()
                                b3=bo2.box()
                                row=b3.row()
                                all_x=[a for a in i.copy_src_track]
                                for x in sorted([a for a in i.copy_src_track if  a.ttype in editable_types and filter_per[a.ttype]==1],key=lambda x:type_sort_order.index(x.ttype)):
                                    
                                    if i.edit_filter!='' and x.name!=i.edit_filter:continue
                                    b4=b3.box()
                                    row=b4.row(align=1)
                                    _o=target_lambda[i.view_mode](x)
                                    #row.label(x.ttype)
                                    if _o==None:continue
                                    row.label(icon=types_icons[x.ttype])
                                    
                                    row.prop(_o,'name',text='' if x.ttype=='Bone' else '')
                                    
                                    if i.info_when_closed and not x.edit_view:
                                        for pii,prop in enumerate(props_info_closed[x.ttype]):
                                            
                                            row.label(str(round(_o[prop],2)),icon=props_icons[prop]) if props_icons.get(prop) else row.label(_o[prop])
                                    if x.ttype=='Bone' and not i.info_when_closed:
                                        idtext=' %s'%('%s (%s)'%(x.changed_id,x.bone_id) if x.changed_id!=0 else x.bone_id)
                                        row.label(idtext)
                                    if len(x.VG)>0:
                                        row.label(str(len(x.VG)),icon='GROUP_VERTEX')
                                        vupd=row.operator('scene.dpmhw_button',text='',icon='STICKY_UVS_VERT')
                                        vupd.func,vupd.var1='refresh_vertex','scene.'+x.path_from_id()

                                    
                                    obse=row.operator('scene.dpmhw_button',text='',icon='HAND' if _o.select else 'DOT')
                                    obse.func,obse.var1='select_object',_o.name
                                    row.prop(x,'edit_view',text='',icon=['VISIBLE_IPO_OFF','VISIBLE_IPO_ON'][x.edit_view])
                                    
                                    if x.edit_view:
                                        row=b4.row()
                                        for pii,prop in enumerate(prop_edit_list[x.ttype]):
                                            if pii in [3,6,9]:row=b4.row(align=1)
                                                
                                            if props_icons.get(prop):row.label(icon=props_icons[prop] )
                                            pp=row.prop(_o,'["%s"]'%prop)


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
                row.prop(_set,'more_obj_options')
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

def refresh_settings(scenelist=[],settings=1,armor=1,event=False):
    if armor:
        with open(base_dir+'\\clothes_num.json','r') as jsr:dict=json.load(jsr)
    if settings:
        with open(json_savepath,'r') as rp:jsr=json.load(rp)
    
    if scenelist==[]:
        scenelist=[s for s in bpy.data.scenes]
    for scene in scenelist:
        mhw=scene.mhwsake
        if armor:
            while len(mhw.armor_num)>0:mhw.armor_num.remove(0)
            for i in dict:
                add=mhw.armor_num.add()
                num,name=i.split('__')
                add.name=name+' (%s)'%num
                add.num=num
        if settings:
            mhw.gamepath=jsr['Global Settings']['gamepath']
            while len(mhw.append_dirs)>0:mhw.append_dirs.remove(0)
            for i in jsr['Global Settings']['BlendAppendPaths']:
                if mhw.append_dirs.get(i)==None:
                    padd=mhw.append_dirs.add()
                    padd.path=i
                    padd.name=i
# def reload_settings(scenelist=[]):
    # if os.path.exists(json_savepath):
       # with open(json_savepath,'r') as rp:jsr=json.load(rp)
       # if scenelist==[]:scenelist=[s for s in bpy.data.scenes]
       # for scene in scenelist:
            # mhw=scene.mhwsake

@persistent
def post_load(scene):

    context = bpy.context
    scene=context.scene
    mhw=scene.mhwsake
    refresh_settings()
    # refresh_armor_numbers()
    # reload_settings()
    #print("WTF")
    #This handler function is ran twice, not sure why,
    #can see it 'WTF' is printed twice.

bpy.app.handlers.load_post.append(post_load)
class dpmhwButton(Operator):
    bl_idname = "scene.dpmhw_button"
    bl_label = "Confirm?"
    name=StringProperty()
    func=StringProperty()
    var1=StringProperty()
    confirmer=BoolProperty(default=0)
    sevent=PointerProperty(type=bpy.types.Event)
    #o2track=PointerProperty(type=ob_copy_track)
    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        self.sevent=event
        if self.confirmer==1:
            return context.window_manager.invoke_confirm(self, event) 
        else:
            return self.execute(context)
    @classmethod
    def update_vg_names(self,col):
                for w in col.VG:
                    ob=w.obje
                    if ob.vertex_groups.get(w.name):
                        ob.vertex_groups[w.name].name=col.o2.name
                        w.name=col.o2.name

    def execute(self,context):
        scene=context.scene
        #wiz=scene.Bwiz
        if self.func=='Save Settings':SaveSettings(context)
        elif self.func=='ApplySettingsToScenes':ApplySettingsToScenes(self.name,context)
        elif self.func=='MHW_Export':MHW_Export(context)
        elif self.func=='MHW_Export_CTC':MHW_Export(context,'CTC')
        elif self.func=='MHW_Export_CCL':MHW_Export(context,'CCL')
        elif self.func=='refresh_armor_numbers':reload_settings(settings=0,event=sevent)
        elif self.func=='reload_settings':reload_settings(armor=0,event=sevent)
        elif self.func=='goto_set_dir': #not implemented yet, go to directory
            goto_set_dir(context)
        elif self.func=='show_info':
            ShowMessageBox(infos[self.var1],'Info','MESH_CUBE')
        elif self.func=='BatchSetsExport':
            BatchSetsExport(context)
        elif self.func=='CopyCTC':
            CopyCTC(self,context,self.var1)
        elif self.func=='ctc_edit_col_edit':
            ctc_edit_col_edit(self,context,self.var1)
        elif self.func=='select_object':
            if bpy.data.objects.get(self.var1):
                ob=bpy.data.objects[self.var1]
                if not self.sevent.shift:bpy.ops.object.select_all(action='DESELECT')

                if ob.hide_select:ob.hide_select=0
                if ob.hide:ob.hide=0
                ob.select=1
                
        elif self.func=='reload_external_ctc':
            reload_external_ctc(self,context)
        elif self.func=='refresh_vertex':
            self.update_vg_names(eval(self.var1))
            self.report({'INFO'},'Succesfully updated vertex groups names by the Bone(empty) names')
        elif self.func=='batch_refresh_vertex':
            col=eval(self.var1)
            for o in [a for a in col.copy_src_track if a.ttype=='Bone']:
               self.update_vg_names(o) 
            self.report({'INFO'},'Succesfully updated vertex groups names by the Bone(empty) names')
        elif self.func=='ctc_copy_over_props':
            col=eval(self.var1)
            ctc_copy_over_props(self,context,col)
        self.confirmer=False
        return {'FINISHED'}
        

        
def register():
    #if post_load in bpy.app.handlers.load_post: return
    global custom_icons

    bpy.utils.register_module(__name__)
    bpy.types.Scene.mhwsake = PointerProperty(type=dpMHW_help)
    #bpy.types.Scene.mhwsetsz=PointerProperty(type=mhwExpSet)
    custom_icons = bpy.utils.previews.new()
    for i in glob.glob(base_dir+'/icons/*.png'):
        custom_icons.load(i.split('\\')[-1][:-4] , i, 'IMAGE')
def unregister():
    global custom_icons
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.mhwsake
    #del bpy.types.Scene.mhwsetsz
    
    for i in custom_icons.values():bpy.utils.previews.remove(i)
    custom_icons.clear()
if __name__ == "mhw_set_organizer":
    register()