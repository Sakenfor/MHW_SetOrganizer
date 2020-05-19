bl_info = {
    "name": "MHW Set Organizer",
    "author": "Sakenfor(dp16)",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "location": "View3D > MOD3 Tools",
    "description": "Helps with various stuff.",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
    }



import bpy,os,sys
import importlib





base_dir = os.path.dirname(os.path.realpath(__file__))
if not base_dir in sys.path:sys.path.append(base_dir)


import mhw_set_organizer

# importlib.reload(dpmhw_arrangers)
# importlib.reload(usual_operators)
importlib.reload(mhw_set_organizer)

def register():
    pass
def unregister():
    pass
