import bpy,glob,os,bmesh
from re import findall
from mathutils import Vector, Matrix

def ObjProp(var,obj,val,descr,max=10.0,min=0.0):
 if not obj==None:
     if not obj.get('_RNA_UI'):
       obj['_RNA_UI'] = {}
     obj[var]=val
     obj['_RNA_UI'][var] = {"description":descr,
          "default": 1.0,
          "min":min,
          "max":max,
          "soft_min":0.0,
          "soft_max":10.0,
          "is_overridable_library":0,
          }

def o_tri(self,scene,object):
            mesh_tri=object.data.copy()
            bm = bmesh.new()
            bm.from_mesh(mesh_tri)
            bmesh.ops.triangulate(bm, faces=bm.faces)
            bm.to_mesh(mesh_tri)
            bm.free()
            object.data=mesh_tri

            mesh_tri.update(calc_tessface=False)
            return mesh_tri

#Alternative to print, good when blender wants to spam constraint loop errors.
def reeport(self,**args):
    rep=[]
    for s in args:rep.append(' %s: %s '%(s,args[s]))
    self.report({'INFO'},', '.join(a for a in rep))
    
def all_heir(ob, levels=25,names=False):
    oreturn=[]
    def recurse(ob, parent, depth):
        if depth > levels: 
            return
        oreturn.append(ob if not names else ob.name)
        for child in ob.children:
            recurse(child, ob,  depth + 1)
    recurse(ob, ob.parent, 0)
    return oreturn

def realignCons(object):
    con=object.constraints.get('Bone Function')
    if con:
        con.inverse_matrix=object.parent.matrix_world.inverted()
        con.target=con.target
        bpy.context.scene.update()

def remove_unused_vg(ob):
    vgroup_used = {i: False for i, k in enumerate(ob.vertex_groups)}
    for v in ob.data.vertices:
        for g in v.groups:
            if g.weight > 0.0:
                vgroup_used[g.group] = True
    
    for i, used in sorted(vgroup_used.items(), reverse=True):
        if not used:
            try:
                ob.vertex_groups.remove(group=ob.vertex_groups[i])
            except:
                pass


def find_col_index(name,collection):
    for i,st in enumerate(collection):
        if st.name==name:
            return i
    return None

def copy_props(sors,tar):
    for k,v in sors.items():tar[k]=v
        #ObjProp(k,tar,v,'')

def copy_various_props(o,o2):
    copy_props(o,o2)
    o2.empty_draw_type=o.empty_draw_type
    o2.show_bounds=o.show_bounds
    o2.show_x_ray=o.show_x_ray

def new_ob(scene,name,mesh=None,link=1):
    o=bpy.data.objects.new(name,mesh)
    if link:
        scene.objects.link(o)
        # scene.update()
    return o

def arma_poll(self,object):
    return object.type=="ARMATURE"
def header_copy_poll(self,object):
    return object.get('Type') and object['Type']=='CTC'
def empty_root_poll(self,object):
    return object.parent==None and object.data==None and object.get('Type')!='CTC'
def mesh_poll(self,object):
    return object.type=='MESH'
def has_att(ob,name,str1=None):
    return ob.get(name) and (str1!=None and ob[name]==str1)

def get_tags(_set,tag_dict=None,where=''):
            tag_dict={} if tag_dict==None else tag_dict
            for a in [z for z in _set.eobjs if z.tag!='' and z.obje!=None and z.accept_weight_transfer]:
                for ta in [s for s in a.tag.split(',') if len(s)>1]:
                    if tag_dict.get(ta)==None:tag_dict[ta]={'Source':[],'Target':[]}
                    tag_dict[ta][where].append(a.obje)
            return tag_dict

def goto_set_dir(context,ppath):
    scene=context.scene
    mhw=scene.mhwsake
    _set=mhw.export_set[mhw.oindex]
    #ppath=_set.export_path
    #if 'nativePC' in ppath:
    ppath=ppath.replace(ppath.split('\\')[-1],'')
    if not os.path.exists(ppath): os.makedirs(ppath)
    os.startfile(ppath)
        
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

def weight_clean(self,context,orga,object):
    do_normalize=orga.normalize_after
    do_limit=orga.limit_after
    do_clean=orga.limit_after
    do_smooth=orga.smooth_after
    if all(x==0 for x in [do_normalize,do_limit,do_clean,do_smooth]):return
    scene=context.scene
    bpy.ops.object.select_all(action='DESELECT')
    object.select=1
    scene.objects.active=object
    scene.update()
    bpy.ops.object.mode_set(mode='OBJECT')
    remove_unused_vg(object)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    limit=None

    if object.data.get('blockLabel')!=None and do_limit:
        ldata=object.data['blockLabel']
        limit=int(findall(r'(?<=IASkin).(?=wt)',ldata)[0])
        try:
            bpy.ops.object.vertex_group_limit_total(limit=limit)
            if limit==4: #Not fully sure if this can cause issues
                object.data['unkn']=19
                object.data['unkn2']=33
                object.data['unkn3']=-61
            elif limit==8:
                object.data['unkn']=19
                object.data['unkn2']=41
                object.data['unkn3']=-61
        except:
            self.report({'WARNING'},'Could not limit the weights of %s'%object.name)
            pass
    if do_smooth:
        bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=orga.smooth_strength, repeat=orga.smooth_count)
        if limit!=None:
            bpy.ops.object.vertex_group_limit_total(limit=limit)
    if do_clean:
        bpy.ops.object.vertex_group_clean(group_select_mode='ALL')

    if do_normalize:
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)

    #bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
def weight_transfer(self,context,source,target,vmap="POLYINTERP_NEAREST"):
    scene=context.scene
    scene.objects.active=target
    target.select=1
    bpy.ops.object.mode_set(mode='OBJECT')
    mname='%s%s'%(source.name,target.name)
    if target.modifiers.get(mname)==None:
        mm = target.modifiers.new(mname, type='DATA_TRANSFER')
    else:mm=target.modifiers[mname]
    mm.use_vert_data=True
    mm.data_types_verts={'VGROUP_WEIGHTS'}
    mm.vert_mapping=vmap
    mm.object=source
    
    bpy.ops.object.datalayout_transfer(modifier=mname)
    try:
        bpy.ops.object.modifier_apply(apply_as='DATA',modifier=mname)

    except:
        self.report({'ERROR'},'Could not apply modifier %s on %s, probably a linked object.'%(mname,target.name))

def fix_ctc_ids(self,context,col):
    scene=context.scene
    arma=col.empty_root
    ctc=col.ctc_header
    if arma ==None or ctc==None:return
    arma_heir=all_heir(arma)
    ctc_heir=all_heir(ctc)
    arma_re={ob.get('boneFunction'):ob for ob in arma_heir}
    #print(ctc_heir)
    for no in ctc_heir:
        
        if no.get('Type')and no['Type']=='CTC_*_Frame':
            
            thenode=no.parent
            kons=thenode.constraints['Bone Function']
            if  kons.target==None:
                nodnum=no['boneFunctionID']
                if arma_re.get(nodnum):
                    node_bone=arma_re[nodnum]
                    kons.target=node_bone
                    kons.inverse_matrix = thenode.parent.matrix_world.inverted()
            else:
                if kons.target.get('boneFunction'):
                    nodnum=kons.target['boneFunction']
                    no['boneFunctionID']=nodnum
                else:
                    self.report({'WARNING'},'Could not find bone function in %s'%kons.target.name)
    scene.update()

def update_sides(self,context,col):
    for i in [a for a in col.copy_src_track if a.ttype=='Bone']:
        loc=i.o2.matrix_world.to_translation()
        i.sideX='R' if loc[0]<0 else 'L' if loc[0]>0 else '0'
        i.sideY='D' if loc[1]<0 else 'U' if loc[1]>0 else '0'
        i.sideZ='B' if loc[2]<0 else 'F' if loc[2]>0 else '0'
        #Right-Left, Down-Up, Back-Front, only L-R is used atm.
        
def find_mirror(o,b_locs):
    if b_locs.get(o)==None or b_locs[o][0][0]==0:return False
    myX=b_locs[o][1]
    closest=[[myX-b_locs[x][0],x['boneFunction']] for x in b_locs if x!=o]
    closest.sort(key=lambda x:x[0])
    return closest[0][1]




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

props_info_closed={'CTC_*_Frame':[],
'CTC':[],
'CTC_Chain':['Snapping','Tension','Weightiness'],
'Bone':['boneFunction'],
'CTC_Node':[],
}

props_icons={'Snapping':'FORCE_HARMONIC',
'Tension':'FORCE_TURBULENCE',
'Wind Multiplier':'FORCE_WIND','boneFunction':'FONT_DATA',
'Weightiness':'MOD_VERTEX_WEIGHT',
'Cone of Motion':'MESH_CONE',
'Gravity Multiplier':'FORCE_CHARGE',

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
                    
                    return o  #if o.o2!=None else None
    else:
        nob=mhw.copy_src_track.add()
        nob.caster=caster

        if add_src!=None:nob.ctc_src=add_src
        if armature!=None:nob.armature=armature
        if o2!=None:
            nob.o2=o2
            nob.name=o2.name
        if caster.get('Type'):# and caster['Type'] in editable_types:
            nob.ttype=caster['Type']
        elif caster.get('boneFunction'):
            nob.ttype='Bone'
            nob.id_name='boneFunction'
        if caster.get('boneFunctionID'):
            nob.id_name='boneFunctionID'
        #print('New object track %s'%ob.name)
        return nob
    return None

def sort_the_tracks(to_sort):
    tracks=[a for a in to_sort.copy_src_track]
    tsort=['Bone','CTC','CTC_Chain','CTC_Node','CTC_*_Frame']
    return sorted(tracks,key=lambda x:tsort.index(x.get('ttype')) if x.get('ttype') in tsort else 9999)

def ctc_copy_over_props(self,scene,col,bones_too=True):

    for o in sort_the_tracks(col):
        copy_props(o.caster,o.o2)
        if o.id_name!='':
            if o.changed_id!=0: #TODO, improve this
                o.o2[o.id_name]=o.changed_id if o.changed_id!=0 else o.bone_id
            elif o.caster.get('boneFunction')!=None:o.bone_id=o.caster['boneFunction']
        if o.ttype=='Bone' and bones_too:
            o.o2.matrix_local=o.caster.matrix_local.copy()
            scene.update()
        elif o.ttype=='CTC_*_Frame':
            o.o2.rotation_euler=o.caster.rotation_euler
        elif o.ttype=='CTC_Node':
            cons=o.o2.constraints.get('Bone Function')
            if cons:
                cons.inverse_matrix = o.caster.parent.matrix_world.inverted()
                scene.update()
    self.report({'INFO'},'Copied properties, preserving the altered boneFunctions, if there were any')

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
    just_file=just_file_str.format(gender=self.gender,armorname2= armorname[2:],armor_part=self.armor_part)
    self.export_path=exp_root+native_add+just_file
    self.import_path=mhw.resource_path+'/chunkG0/'+native.replace('\\nativePC\\','')+just_file

def upd_base_paths(self,context):
    scene=context.scene
    mhw=scene.mhwsake
    for _set in mhw.export_set:
        upd_exp_path(_set,context)

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
,'ctc_copy_over_props':
'''
Copying the props from sources, will preserve
the shifted boneFunctions if there are any, on Frame and Bone.

'''
,'ctc_after_copy':
'''
Ticking this, after ctc has been copied, it will look for Set from which
the CTC Source was, and check for 'tags' of source set objects, and tags
of active set, and transfer weights of bones ABOVE 150 number,
between the objects that had same tag.


'''
 }

##Copied from Asterisk's CTC Tools, modified for easier use without bpy.ops:
accessScale = lambda scaleVector: scaleVector[0]
def orientVectorPair(v0,v1):
    v0 = v0.normalized()
    v1 = v1.normalized()
    if v0 == v1:
        return Matrix.Identity(3)
    v = v0.cross(v1)
    #s = v.length
    c = v0.dot(v1)
    if c == -1: return Matrix([[-1,0,0],[0,-1,0],[0,0,1]])
    vx = Matrix([[0,-v[2], v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
    return Matrix.Identity(3)+vx+(1/(1+c))*vx*vx
    
def normalProjection(normal,vector):
    return vector - vector.dot(normal)/normal.length**2*normal
def orientVectorSystem(star,target,axis):
    sscale = star.empty_draw_size*accessScale(star.matrix_world.to_scale())
    star.empty_draw_size = sscale
    loc = star.location
    targetVector = target.matrix_world.translation-star.matrix_world.translation
    M = orientVectorPair(axis,targetVector)
    star.matrix_local = M.to_4x4()
    star.location = loc


def pointFrameTo(self,object,point_to):
        vec=Vector([1,0,0])
        orientVectorSystem(object,point_to,vec)
        
################### End of Point Frame To Copied-Altered Section

def fAlignVarious(self,target,align_frames=0,align_nodes=0): #Used in Export CTC only so far
    if align_frames==0 and align_nodes==0:return
    ctchil=all_heir(target)
    node_d,frame_d={},{}
    for ob in ctchil:
        if ob.get('Type')=='CTC_*_Frame' and align_frames:
            frame_d[ob]=ob.parent.parent
            node_d[ob.parent]=ob
        if ob.get('Type')=='CTC_Node' and align_nodes:
            realignCons(ob)
    for frame in frame_d:
        nod=frame_d[frame]
        if node_d.get(nod):
            to_point=node_d[nod]
            pointFrameTo(self,to_point,frame)