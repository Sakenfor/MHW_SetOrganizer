import bpy,os,sys,bmesh
from bpy.props import EnumProperty,StringProperty,PointerProperty,IntProperty,BoolProperty
from bpy.types import Operator
from mathutils import Matrix,Vector
sys.path.append("..")
from general_functions import *
import random
from re import findall
chrs = 'abvgddjezzijklmnjoprstcufhccdzsh0123456789'


    

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

def CopyCTC(self,context,copy_from,source,src_heir,ctc_organizer,source_set,tag_dict): #AKA, The Most Messy Code You Have Ever Seen.
    scene=context.scene
    mhw=scene.mhwsake
    _set=mhw.export_set[mhw.oindex]
    found_root=None
    changed_ids,b_ids={},{}
    new_bonedict={}
    rigname='MHW Statyk %s Character Rig'%{'f':'Female','m':'Male'}[_set.gender]
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
    for ch in ctc_organizer.entries:
        if not ch.toggle:
            #src_heir.remove(ch.chain)
            for ci in all_heir(ch.chain):src_heir.remove(ci)
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
            if len(hier)<3:continue
            if found_root==None:
                found_root=hier[-2]
                src_bone_hier=all_heir(found_root)
                src_arma={a:a.get('boneFunction') for a in src_bone_hier}
                src_arma_re={a.get('boneFunction'):a for a in src_bone_hier}
    if copy_from!='Local':
        for h in bone_additional+src_heir:
            try:
                sob.link(h)
            except:
                pass
    if target==None:
        self.report({'ERROR'},'Missing; Source: %s, Target %s'%(str(source),str(target)))
        return
    valid_obs=[a for a in _set.eobjs if a.export==1 and a.obje!=None and a.obje.name in scene.objects]
    bone_additional=list(set([a for a in bone_additional if a!=None and  a.get('boneFunction')!=None]))

    if not any(s.source==source for s in _set.ctc_copy_src):
        ctc_col=_set.ctc_copy_src.add()
        ctc_col.name=source.name
        ctc_col.source=source
        ctc_col.target=target
    else:
        for i in _set.ctc_copy_src:
            if i.source==source:
                ctc_col=i
    if ctc_organizer.copy_ctc_bool:
        #_src=all_heir(source)
        fmax=max(list(arma[a] for a in arma if arma[a]!=None))+1
        
        text_prep,text_new=mhw.header_copy_name,mhw.header_new_names
        _obs=bpy.data.objects
        count_types={'Bone':1,'Header':1,'Frame':1,'Chain':1,'Node':1}
        ctcO.obs={'Bone':{},'Header':{},'Frame':{},'Chain':{},'Node':{}}
        
        total_list=bone_additional+src_heir
        b_locs={}
        for bo in bone_additional:
            bm=bo.matrix_world.to_translation()
            b_locs[bo]=[bm,Vector([-bm[0],bm[1],bm[2]])]
            

        list_max_id2=[]
        for isr,o in enumerate(src_heir ):
            if o.get('Type') and o['Type']=='CTC_Node':
                pco=[a for a in o.constraints if a.type=='CHILD_OF']
                if pco==[]:
                    continue
                else:pco=pco[0]
                if pco.target==None:continue
                nodebone=pco.target
                total_list.insert(0,nodebone)
                if nodebone.parent!=None and nodebone.parent not in total_list:total_list.insert(0,nodebone.parent)
                
                list_max_id2.append(nodebone['boneFunction'])
            if header_tar==None and o.get('Type') and o['Type']=='CTC':
                header_tar=o
        max_id2=max(list_max_id2) if list_max_id2!=[] else 0
        order=total_list[:]
        total_list=sorted(list(set(total_list)),key=lambda x:order.index(x))
        #remove doubles,preserve sort order, crucial else parenting is messed, is a current flaw ^
        if max_id2>fmax:fmax=max_id2+1
        elif max_id2==fmax:fmax=fmax+1
    for xx in _set.ctc_copy_src:
        if xx.target!=target:continue
        for a in xx.copy_src_track:
            if a.ttype=='CTC':
                header_tar=a.caster
                if header_tar.name not in scene.objects:scene.objects.link(header_tar)
            if a.ttype!='Bone' or a.bone_id==0:continue
            b_ids[a.bone_id]=a
            if a.changed_id!=0:changed_ids[a.bone_id]=a
            if a.caster!=None and a.o2!=None:new_bonedict[a.caster.name]=a.o2

    pairs,frame_props,to_parent,pairs2={},{},{},{}
    li=bpy.data.libraries.data.objects
    if ctc_organizer.copy_ctc_bool:
        for isr,o in enumerate(total_list):
            if o==None:continue
            om=o.matrix_world.copy()
            mirror=False
            if o.get('Type') and regular_ctc_names.get(o['Type']):tty=regular_ctc_names[o['Type']]
            else:tty='Bone'
            if header_tar!=None and header_tar!=o and tty=='Header':
                _o2=ctcO(tty=tty,o=o,o2=header_tar)
                o2track=ob_in_track(ctc_col,o,armature=target,report=self)
                if o2track==None:o2track=ob_in_track(ctc_col,o,source,target,header_tar)
                #self.report({'INFO'},'HEADER %s'%header_tar.name)
                continue
            
            if text_new=='':
                obn='%s%s'%(text_prep,o.name)
                
            else:
                obn='%s%s'%(text_new,count_types[tty] if tty!='Header' else '')
            rem_num=findall(r'\.[0-9]*',obn)
            if rem_num and rem_num[0]!='.':obn=obn.replace(rem_num[0],'')
            osp=o.name.split('.')
            ext='.R' if '.R' in o.name else '.L' if '.L' in o.name else ''
            count_types[tty]+=1
            if tty not in obn:obn='%s_%s'%(tty,obn) if not mhw.type_infront else '%s_%s'%(obn,tty)
            new,o2=0,None
            if mhw.ctc_copy_add_LR:
                obn=obn.replace(ext,'')
                ext=''
            o_id=o_id_b=o.get('boneFunction')
            #if changed_ids.get(o_id):o_id=changed_ids[o_id].changed_id
            o2track=ob_in_track(ctc_col,o,armature=target,report=self)
            if tty=='Bone':

                if changed_ids.get(o_id):
                    o2track=changed_ids[o_id]
                    o2=o2track.o2
                elif b_ids.get(o_id):
                    o2track=b_ids[o_id]
                    o2=o2track.o2
                elif arma_re.get(o_id) and o_id<150:
                    o2=arma_re[o_id]
                    if o2track==None:
                        o2track=ob_in_track(ctc_col,o,source,target,o2)
                
                mirror=find_mirror(o,b_locs)
                if mirror:
                    m_id=str(mirror+o_id)
                    if pairs.get(m_id):obn=pairs[m_id]
                    else:pairs[m_id]=obn
            if source==header_tar:o2=o
            if o2track==None:
                new=1
                obx=obn#=obn.replace(ext,'')
                #
                if o_id_b!=None and mhw.ctc_copy_add_LR and o_id_b>=150 and ext=='':
                    obn=obn.replace('.R','').replace('.L','')
                    if  all(not obn.endswith(x) for x in ['.L','.R']) and ext=='':
                        tbone_X=om.to_translation()[0]
                        if tbone_X<0:ext='.R'
                        elif tbone_X>0:ext='.L'
                obn=obn+ext
                if bpy.data.objects.get(obn)!=None or li.get(obn)!=None:
                    nnum=1

                    while bpy.data.objects.get(obn)!=None  or li.get(obn)!=None:
                        nn='.%03d'%nnum
                        obn=obx+nn+ext
                        nnum+=1
                    #obn=obn+'.%03d%s'%(nnum,ext)
                else:obn=obn
                # if tty=='Bone' and 
                #if arma_re.get(o_id_b) and tty=='Bone' and o2==None and o_id_b<150:o2=arma_re[o_id_b]
                if o2==None:
                    o2=new_ob(scene,obn)
                o2track=ob_in_track(ctc_col,o,source,target,o2)
                o2track.name=o2.name
                if tty=='Bone':
                    #reeport(self,bo=o2.name,id=o_id)
                    #if 
                    #pid=source_bone_hie[o_id]
                    if o2track.bone_id==0:o2track.bone_id=o_id
                    if o_id >= 150 and arma_re.get(o_id)!=None and source!=header_tar: #and o2track.is_new==1:
                       
                        if o2track.changed_id==0:
                            #o_id=fmax
                            o2track.changed_id=o_id
                            self.report({'INFO'},'Shifted boneFunction %s to %s (%s)'%(o['boneFunction'],fmax,o2.name))
                            o2track.bone_id=fmax
                            fmax+=1
            
            elif o2track.changed_id==0 and o_id!=None:o2track.bone_id=o_id
            if tty=='Bone' and mirror and o2track.o2!=None:
                if pairs2.get(m_id)==None:pairs2[m_id]=[]
                pairs2[m_id].append(o2)
            # if changed_ids.get(pid):o2track.caster=changed_ids[pid]
                    # b_ids[o_id]=o2track
            
            if tty=='Header':headerr=o2
        if _set.ctc_header==None:
            _set.ctc_header=headerr
            #self.report({'WARNING'},'%s - set header has been set to source copied header.'%_set.ctc_header.name)

    
    tr_all_wgt=1
    scene.update()

    if tr_all_wgt:
        for sr in src_arma_re:
            if sr==None:continue
            if arma_re.get(sr):new_bonedict[src_arma_re[sr].name]=arma_re[sr]
            if changed_ids.get(sr) and changed_ids[sr].caster==src_arma_re[sr]:
                tname=changed_ids[sr].o2
            # elif arma_re.get(sr) and changed_ids.get(sr)==None:
                # tname=arma_re[sr]
                
            else:continue
            #if new_bonedict.get(src_arma_re[sr].name)==None:
            new_bonedict[src_arma_re[sr].name]=tname
            
    sorted_tracks=sort_the_tracks(ctc_col)
    if ctc_organizer.copy_ctc_bool:
        for i in sorted_tracks:
            #if o==None or o2==None:continue
            o,o2=i.caster,i.o2
            #om=
            #if i.bone_id==0 and i.ttype=='Bone':continue
            pa=[a for a in ctc_col.copy_src_track if a.caster==o.parent]
            if pa!=[]:
                try:
                    o2.parent=pa[0].o2
                except:
                    self.report({'WARNING'},'Could not set parent for %s for some reason :s !'%o2.name)
            
            else:
                if i.bone_id>=150:
                    self.report({'WARNING'},'Could not find parent of %s!'%o2.name)
            #o2.matrix_world=Matrix()
            copy_various_props(o,o2)
            #scene.update()
            
            if i.ttype=='Bone':
                #if o.parent==None:
                new_bonedict[o.name]=o2
                o2.matrix_local=o.matrix_local.copy()
                IDD=i.bone_id #if i.changed_id==0 else i.changed_id
                o2['boneFunction']=IDD
                scene.update()
            elif i.ttype=='CTC_*_Frame':
                o2.rotation_euler=o.rotation_euler
                fpar=[a for a in ctc_col.copy_src_track if o2.parent == a.o2]
                if fpar!=[]:
                    kID=fpar[0].o2.constraints['Bone Function'].target['boneFunction']
                    o2['boneFunctionID']=kID
            
            elif i.ttype=='CTC_Node':
                korig=o.constraints['Bone Function']
                if o2.constraints.get('Bone Function')==None:
                    cons=o2.constraints.new(type='CHILD_OF')
                    cons.name='Bone Function'
                else:cons=o2.constraints['Bone Function']
                findbo=[a for a in ctc_col.copy_src_track if a.caster==korig.target]
                cons.target=findbo[0].o2
                cons.inverse_matrix = o2.parent.matrix_world.inverted()

            scene.update()
    modif_state_save,ob_state_save={},{} #TODO, choose to use modifiers or not

    if ctc_organizer.transfer_weights :
        for ttag in tag_dict:
            tag=tag_dict[ttag]
            if tag['Target']==[] or tag['Source']==[]:continue

            for s in tag['Target']+tag['Source']:
                ob_state_save[s.obje]=[s.obje.hide,s.obje.hide_select]
                s.obje.hide=0
                s.obje.hide_select=0
                for m in [a for a in s.obje.modifiers if a.type!='SUBSURF']:
                    modif_state_save[m]=m.show_viewport
                    m.show_viewport=0
            for _s in tag['Source']:
                s=_s.obje
                #mco=s.data.copy()
                oco=s.copy()#new_ob(s.name+'_weight_source',mco)
                mcopy=s.data.copy()
                oco.data=mcopy
                
                scene.objects.link(oco)
                scene.update()
                
                del_mat_slots = []
                m_list={m.name:i for i,m in enumerate(s.material_slots)}
                for m in [a for a in ctc_organizer.trf_mat_ch if a.obje==s]:
                    ma=m.mate.name
                    if ma in s.material_slots and m.toggle==False:
                        del_mat_slots.append(m_list[ma])
                if del_mat_slots: #Same as del_mat_slots!=[]
                    faces2del = []
                    bm = bmesh.new()
                    bm.from_mesh(mcopy)

                    for face in bm.faces:
                        if face.material_index in del_mat_slots:
                            faces2del.append(face)
                            
                    bmesh.ops.delete(bm, geom=faces2del, context=5)
                    bm.to_mesh(mcopy)
                    bm.free()
                    
                wgt_rem_rng=ctc_organizer.rem_vg_b4_range
                wgRangeLambda=lambda x:x==x if wgt_rem_rng=='All Groups' else lambda x:x['boneFunction']<150 if wgt_rem_rng=='Below 150 ID' else lambda x:x['boneFunction']>=150
                for w in oco.vertex_groups:
                    if new_bonedict.get(w.name):
                        w.name=new_bonedict[w.name].name
                        if ctc_organizer.remove_vg_before_transfer:
                            for _o in tag['Target']:#valid_obs:
                                o=_o.obje
                                #reeport(self,v1=o.obje.vertex_groups.get(w.name),v2=bpy.data.objects[w.name]['boneFunction']>=150,ob=o.obje.name)
                                if o.vertex_groups.get(w.name) and wgRangeLambda(bpy.data.objects[w.name]):
                                    o.vertex_groups.remove(group=o.vertex_groups[w.name])
                    else:
                        oco.vertex_groups.remove(w)
                        continue

                    if ctc_organizer.wgt_limit=='All Groups':continue
                    bo=bpy.data.objects[w.name]
                    bool1=bo['boneFunction']>=150 and ctc_organizer.wgt_limit=='Below 150 ID'
                    bool2=bo['boneFunction']<150 and ctc_organizer.wgt_limit=='Above 150 ID'
                    if bool1 or bool2:oco.vertex_groups.remove(w)
                        
                for _t in tag['Target']:
                    t=_t.obje
                    if t.name not in scene.objects:continue
                    weight_transfer(self,context,oco,t,bmesh_grp=ttag if (_t.tags.get(ttag) and _t.tags[ttag].use) else False)
                    # if _set.normalize_active:
                        # t.select=1
                        # scene.update()
                        # bpy.ops.object.mode_set(mode='EDIT')
                        # bpy.ops.mesh.select_all(action='SELECT')
                        # for vg in new_bonedict:
                            # vgn=new_bonedict[vg]
                            # if t.vertex_groups.get(vgn):
                                # t.vertex_groups.active_index=t.vertex_groups.find(vgn)
                                # bpy.ops.object.vertex_group_normalize_all(lock_active=True)
                        # bpy.ops.object.mode_set(mode='OBJECT')
                
                bpy.data.objects.remove(oco)
                bpy.data.meshes.remove(mcopy)
        if ctc_organizer.remove_vg_not_found:
            if bpy.data.objects.get(rigname)!=None:
                aux_bones=[a.name for a in bpy.data.objects[rigname].pose.bones]
            else:aux_bones=[]
            all_bones=all_heir(target,names=1)
            for t in [a for a in _set.eobjs if a!=None]:
                remvg=[]
                for vg in t.obje.vertex_groups:
                    if vg.name not in all_bones and vg.name not in aux_bones:
                        remvg.append(vg.name)
                        t.obje.vertex_groups.remove(group=vg)
                if remvg!=[]:self.report({'INFO'},"Object %s, removed unused groups: %s"%(t.obje.name,', '.join(a for a in remvg)))
            
        
        for t in tag['Target']:

            weight_clean(self,context,ctc_organizer,t.obje)

        for m in modif_state_save:m.show_viewport=modif_state_save[m]
        for i in ob_state_save:i.hide,i.hide_select=ob_state_save[i]
    update_sides(self,context,ctc_col)
    
    for mbo in pairs2:
        if len(pairs2[mbo])!=2:continue
        _x1,_x2=pairs2[mbo]
        co1=ctc_col.copy_src_track[_x1.name]
        co2=ctc_col.copy_src_track[_x2.name]
        #Had to be done this way, for some reason stroing a copy_src_track in array gave violation access error
        co1.pair=_x2
        co2.pair=_x1

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
        _set=mhw.export_set[mhw.oindex]
        sobs=[a.obje for a in _set.eobjs if a.obje!=None]
        # A bit rough way to delete a collection but idea was a universal delete button
        delwhat,delnum,delhow=self.col_path,self.col_num,self.del_how
        delwhat=eval(delwhat)
        to_rem=delwhat[delnum]
        to_rem_name=to_rem.name
        bremoved=[]
        if delhow=='delete_ctc':
            for o in to_rem.copy_src_track: #[a for a in to_rem.copy_src_track if a.is_new]:
                if o.ttype=='Bone':
                    if self.remove_vg:
                        for obj in sobs:
                            if obj.vertex_groups.get(o.name):
                                obj.vertex_groups.remove(obj.vertex_groups[o.name])
                    if self.keep_bones:continue
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
        row=self.layout
        row.prop(self,'remove_vg',text='Remove Vertex Groups Associated?',icon='SNAP_VERTEX')

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
            bpy.context.scene.render.engine = 'CYCLES'

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
useful_modifiers=['HOOK']
class safeRemoveDoubles(Operator): 
    """Safely merge double vertices, hold Shift to choose last chosen options"""
    bl_idname = "dpmhw.safedoubleremove"
    bl_label = "Safely Remove Double Vertices"
    bl_options = {"REGISTER", "UNDO"} 
    
    pres_methods=[['Normals Split','Use the split normals modifier','MOD_NORMALEDIT'],
    ['Normals Transfer','Use the transfer normals modifier','OBJECT_DATA']]
    tar_ob=StringProperty()
    pres_method=EnumProperty(default='Normals Transfer',items=[(a[0],a[0],a[1],a[2],x) for x,a in enumerate(pres_methods)])
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        if bpy.data.objects.get(self.tar_ob)!=None:
            scene=context.scene
            oob=bpy.data.objects[self.tar_ob]
            mosave={m:m.show_viewport for m in oob.modifiers if m.type !='SUBSURF'}
            for m in mosave:m.show_viewport=False
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
            bpy.ops.mesh.select_all(action='DESELECT')
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
            for m in mosave:m.show_viewport=mosave[m]
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
            mosave={m:m.show_viewport for m in oob.modifiers if m.type !='SUBSURF'}
            for m in mosave:m.show_viewport=False
            bpy.ops.mod_tools.solve_uv_rep()
            for o in selsave:o.select=1
            context.scene.objects.active=aktsave
            oob.hide,oob.hide_select=osave
            for m in mosave:m.show_viewport=mosave[m]
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
    func=StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        scene=context.scene
        _set=eval(self.var1)
        if self.func=='show_toggle':
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
        elif self.func=='hideselect_toggle':
            total_list=[a.obje for a in _set.eobjs if a.obje !=None]
            for o in total_list:
                o.hide_select=_set.toggler_hideselect
            if _set.toggler_hideselect:_set.toggler_hideselect=False
            else:_set.toggler_hideselect=True
        return {'FINISHED'}
    def invoke(self, context, event):
        self.ev=event
        return self.execute(context)

def set_choose_dynamic(self,context):
    global enum_sets
    items=[(a[0],a[0],a[1],a[2],x) for x,a in enumerate( enum_sets)]
    return items
    
class updateUsersOfCTC(Operator):
    """Could not think of what to write here"""
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
        
        
        row.prop(self,'set_choosing',text='Choose Target(s)')
        #row.prop_search(self,'tar_ob',context.scene,'objects',text='Target')
        row=self.layout
        row.prop(self,'bones_too',text='Copy bone matrices too?',icon='GROUP_BONE')


class CopyCTCops(Operator):
    """Copy CTC Header or Chains"""
    bl_idname = "dpmhw.ctc_copier"
    bl_label = "Copy CTC"
    bl_options = {"UNDO"} 
    
    copy_from=StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        scene=context.scene
        
        CopyCTC(self,context,self.copy_from,self.source,self.source_heir,self._org,self.source_set,self.tag_dict)
        return {'FINISHED'}
    def invoke(self, context, event):
        scene=context.scene
        mhw=scene.mhwsake
        _set=self._set=mhw.export_set[mhw.oindex]
        orga=_set.ctc_organizer
        copy_from=self.copy_from
        
        if copy_from=='Local':
            source=_set.header_copy_source
            #src_heir=all_heir(source)
        else:
            src=_set.ext_header_copy_name
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
            if bpy.data.scenes.get(portscene)==None:sc2=bpy.data.scenes.new(name=portscene)
            else:sc2=bpy.data.scenes[portscene]
            sob=sc2.objects
            #scene.objects.link(heade)
            source=heade
            src_heir=all_heir(heade)
            #source=sc2.objects[heade.name]
        #self.source,self.src_heir=source,src_heir
        if source==None:return{'FINISHED'}
        self.source=source
        _org=None
        for i in orga:
            if i.source==source:
                _org=i
                break
        if _org==None:
            _org=orga.add()
            _org.source=source
        entries=[a.chain for a in _org.entries]
        self.source_heir=source_heir=[a for a in all_heir(source) ]
        src_chains=[a for a in source_heir if a.get('Type') and a['Type']=='CTC_Chain']
        
        to_del=[]
        for ee in _org.entries:
            if ee.chain not in src_chains: to_del.append(ee)
        for i in to_del:_org.entries.remove(i)
        for he in src_chains:
            if he not in entries:
                newE=_org.entries.add()
                newE.chain=he
        self._org=_org
        
        self.source_set=None
        self.tag_dict=get_tags(_set,where='Target')
        for s in bpy.data.scenes:
            for se in s.mhwsake.export_set:
                if se.ctc_header==source and source!=None:
                    self.source_set=se
                    self.tag_dict=get_tags(se,self.tag_dict,where='Source')
                    break
        if self.source_set!=None:
            sso=self.source_set
            mat_list=[]
            for t in self.tag_dict:
                for o in self.tag_dict[t]['Source']:
                    mat_list.extend([o.obje,m.material] for m in [x for x in o.obje.material_slots if x!=None and x.name!='']   )
                
            for obje,mate in mat_list:
                mcode='%s: %s'%(obje.name,mate.name)
                if  all([obje,mate]!=[_u.obje,_u.mate] for _u in _org.trf_mat_ch) or len(_org.trf_mat_ch)==0:  
                #if _org.trf_mat_ch.get(mcode)==None:
                    iadd=_org.trf_mat_ch.add()
                    iadd.name=mcode
                    iadd.obje=obje
                    iadd.mate=mate
            m_rem=[i for i,_i in enumerate(_org.trf_mat_ch) if [_i.obje,_i.mate] not in mat_list]
            for i in m_rem:_org.trf_mat_ch.remove(i)
                
        
        return context.window_manager.invoke_props_dialog(self)
        
    def draw(self, context):
        # row=self.layout
        _set=self._set
        _org=self._org
        layout=self.layout
        row=layout.row()
        row.label("Weights, CTC-Chains Copy, or Both:")
        row=layout.row()
        row.prop(_org,'transfer_weights',icon='MOD_VERTEX_WEIGHT',text='Transfer Weights')
        row.prop(_org,'copy_ctc_bool',icon='ROTATECENTER',text='Copy CTC')
        help1=row.operator("scene.dpmhw_button", icon='QUESTION', text="")
        help1.var1,help1.func='ctc_after_copy','show_info'
        row=layout.row()
        row.label('After Transfer Weights, Do:')
        row=layout.row()
        bo1=row.box()
        row=bo1.row()
        row.prop(_org,'limit_after',text='Limit 4/8',icon='LINENUMBERS_ON')
        row.prop(_org,'clean_after',text='Clean',icon='SNAP_NORMAL')
        row.prop(_org,'normalize_after',text='Normalize All',icon='MOD_NORMALEDIT')
        row=bo1.row(align=1)
        row.prop(_org,'smooth_after',text='Smooth Weights',icon='MOD_SMOOTH')
        row.prop(_org,'smooth_strength',text='Strength')
        row.prop(_org,'smooth_count',text='Repeat')

        
        row=layout.row()
        row.prop(_org,'wgt_limit')
        row=layout.row()
        row.label('Remove Vertex Groups..')
        row=layout.row()
        row.prop(_org,'remove_vg_not_found',icon='GROUP_VERTEX',text='..Not Found in Bones')
        row=layout.row()
        row.prop(_org,'remove_vg_before_transfer',icon='GROUP_VERTEX',text='..Before Weight Transfer')
        row.prop(_org,'rem_vg_b4_range',text="")
        row=layout.row()
        
        ebox=row.box()
        row=ebox.row()
        row.label('Choose chains to copy')
        
        for i in _org.entries:
            row=ebox.row()
            row.prop(i,'toggle',text=i.chain.name,icon=['PMARKER','PMARKER_SEL'][i.toggle])
        row=layout.row()

        col = row.column(align=True)
        row.label('Toggle weight transfer by materials')
        row=layout.row()
        row.template_list("dpMHW_drawMaterialChoiceCTC", "", _org, "trf_mat_ch", _org, "oindex", rows=2)

class BoneMirrorer(Operator): 
    """Mirror objects from L>R or R>L"""
    bl_idname = "dpmhw.mirror_bones"
    bl_label = "Mirror Bones"
    bl_options = {"REGISTER", "UNDO"} 
    copyid=StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        
        ctcopy=self.ctcopy
        update_sides(self,context,ctcopy)
        if ctcopy.lr_LR=='L>R':lambd_find=lambda x:x.sideX=='L'
        elif ctcopy.lr_LR=='R>L':lambd_find=lambda x:x.sideX=='R'
        
        sources=[a for a in ctcopy.copy_src_track if a.ttype=='Bone' and lambd_find(a)]
        for so in sources:
            if so.pair==None:continue
            sma=so.o2.matrix_local
            sotr=sma.to_translation()
            soro=sma.to_euler()
            _tr=[-sotr[0],sotr[1],sotr[2]]
            _ro=[soro[0],-soro[1],-soro[2]]
            so.pair.location=_tr
            so.pair.rotation_euler=_ro
            so.pair.scale=so.o2.scale
            if ctcopy.lr_insert_kf:
                for ob in [so.o2,so.pair]:
                    ob.keyframe_insert(data_path='location')
                    ob.keyframe_insert(data_path='rotation_euler')
                    ob.keyframe_insert(data_path='scale')
        return {'FINISHED'}
    def invoke(self, context, event):
        scene=context.scene
        self.ctcopy=ctcopy=eval(self.copyid)

        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        ctcopy=self.ctcopy
        row=self.layout
        row.prop(ctcopy,'lr_LR',text='From-To')
        row=self.layout
        row.prop(ctcopy,'lr_insert_kf',icon='KEYTYPE_KEYFRAME_VEC')


class WeightTransferAssigner(Operator): 
    """Assign vertices to weight transfer TAG"""
    bl_idname = "dpmhw.wgt_trfer_asgn"
    bl_label = "Assign Vertices"
    bl_options = {"REGISTER", "UNDO"} 
    
    obje=StringProperty()
    assign_name=StringProperty()
    deselect_after=BoolProperty()
    func=StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        
        obj=self.obj
        o=obj.obje
        asign=self.assign_name
        scene=bpy.context.scene

        if self.func in ['ASSIGN','SELECT']:
            ###
            scene.objects.active=o
            o.select=1
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(o.data)
            bm.verts.ensure_lookup_table()
            me=o.data
            ###
            if self.func=='ASSIGN':
                my_id = (bm.verts.layers.int.get(asign) or 
                    bm.verts.layers.int.new(asign))
                
                for v in bm.verts:
                    v[my_id] = 1 if v.select else 0
                bm.verts.ensure_lookup_table()
                bmesh.update_edit_mesh(o.data)
                
                if self.deselect_after:bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                if obj.tags.get(asign)==None:
                    aadd=obj.tags.add()
                    aadd.name=asign

            elif self.func=='SELECT':
               if asign in bm.verts.layers.int:
                    vlayer = bm.verts.layers.int[asign]
                    zz=[v.index for v in me.vertices if 
                            bm.verts[v.index][vlayer]==1]
               bpy.ops.object.mode_set(mode='OBJECT')
               for u in zz:me.vertices[u].select=True
               bpy.ops.object.mode_set(mode='EDIT')
        elif self.func=='REMOVE_TAG':
            obj.tags.remove(asign)
        
        return {'FINISHED'}
    def invoke(self, context, event):
        scene=context.scene
        self.obj=obj=eval(self.obje)

        #bpy.ops.object.select_all(action='DESELECT')

        
        if self.func=='ASSIGN':
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)
    def draw(self, context):
        row=self.layout
        row.prop(self,'deselect_after',icon='BORDER_LASSO',text='Deselect All Verts After')
        pass


cls=[SimpleConfirmOperator,CopyObjectChangeVG ,
SolveRepeatedUVs,safeRemoveDoubles,
MHW_ImportManager,emptyVGrenamer,
updateUsersOfCTC,SetObjectsToggler,
SaketargetArmature,SaketargetEmpties,CopyCTCops,
BoneMirrorer,WeightTransferAssigner,

]
def register():
    for cl in cls:
        bpy.utils.register_class(cl)

def unregister():
    for cl in cls:
        bpy.utils.unregister_class(cl)
if __name__ == "operators.usual_operators":
    register()