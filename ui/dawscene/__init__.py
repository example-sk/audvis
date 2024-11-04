from xml.etree.ElementTree import Element

import bpy
import zipfile
import pathlib
import bpy_extras
from xml.etree import ElementTree

from .parser import dawproject
from .scene import Scene
from ..buttonspanel import AudVisButtonsPanel_Npanel


class AUDVIS_OT_DawSceneTo3D(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "audvis.dawsceneto3d"
    bl_label = "Import DAW Scene"

    filepath: bpy.props.StringProperty(name=".dawscene file path", subtype='FILE_PATH', options={'SKIP_SAVE'})
    # filter_search: bpy.props.StringProperty(default="*.dawscene", options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(
        default="*.dawproject",
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        self.filter_search = '*.dawproject'
        return {'RUNNING_MODAL'}

    def _render(self, context, dawscene: Scene):
        scene = context.scene
        if 'dawscene' not in bpy.data.node_groups:
            libpath = pathlib.Path(__file__).parent.resolve().__str__() + "/dawscene-blender3_6.blend"
            with bpy.data.libraries.load(libpath) as (data_from, data_to):
                data_to.materials = data_from.materials
                data_to.node_groups = data_from.node_groups
        mesh = self._init_mesh(dawscene)
        y = 0.0
        for track in dawscene.tracks:
            y = y + .1
            for clip in track.clips:
                mesh.vertices.add(1)
                mesh.update()
                vertex = mesh.vertices[-1]
                vertex.co[0] = float(clip.time)
                vertex.co[1] = -y
                mesh.attributes['width'].data[-1].value = float(clip.duration)
                mesh.attributes['height'].data[-1].value = float(.1)
                mesh.attributes['layer'].data[-1].value = 1
                mesh.attributes['clr'].data[-1].color = clip.color

        obj = bpy.data.objects.new('dawscene', mesh)
        scene.collection.objects.link(obj)
        mod = obj.modifiers.new(name="dawscene", type="NODES")

        mod.node_group = bpy.data.node_groups['dawscene']
        keyframe_path = mod.path_from_id('["Input_5"]')
        mod['Input_5'] = 0.0
        obj.keyframe_insert(data_path=keyframe_path, frame=1)
        mod['Input_5'] = 1.0
        obj.keyframe_insert(data_path=keyframe_path, frame=100)

    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
        parsed_scene = None
        if self.filepath.endswith(".dawproject"):
            parsed_scene = dawproject.parse(self.filepath)
        # TODO: add other DAWs
        else:
            return {'CANCELLED'}
        self._render(context, parsed_scene)
        return {'FINISHED'}

    def _init_mesh(self, dawscene: Scene):
        mesh = bpy.data.meshes.new(dawscene.name if dawscene.name is not None else 'dawscene')
        mesh.attributes.new('width', 'FLOAT', 'POINT')
        mesh.attributes.new('height', 'FLOAT', 'POINT')
        mesh.attributes.new('layer', 'INT', 'POINT')
        mesh.attributes.new('clr', 'FLOAT_COLOR', 'POINT')
        return mesh


def _parse_color(input: str):
    tmp = input.lstrip('#')
    return (
        int(tmp[0:2], 16) / 255,
        int(tmp[2:4], 16) / 255,
        int(tmp[4:6], 16) / 255,
        1,
    )


class AUDVIS_PT_DawprojectTo3d(AudVisButtonsPanel_Npanel):
    bl_label = "Import DAWscene"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align=True)
        col.operator('audvis.dawsceneto3d')


classes = [
    AUDVIS_OT_DawSceneTo3D,
    AUDVIS_PT_DawprojectTo3d,
]
