import pathlib

import bpy

from .outputs import (geometrynodes1)
from .parser import (dawproject, als, audiofile)
from .arrangement import Arrangement
from ..buttonspanel import AudVisButtonsPanel_Npanel
from ..props.daw_arrangement import AudvisDawArrangement

supported_audio_extensions = (".mp3", ".wav", ".aif", ".aiff", ".ac3", ".aac", ".opus", ".mp2", ".ogg", ".flac")

# class AUDVIS_OT_DawArrangementTo3D(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
class AUDVIS_OT_DawArrangementTo3D(bpy.types.Operator):
    bl_idname = "audvis.dawarrangementto3d"
    bl_label = "Import DAW Arrangement"
    bl_options = {'UNDO'}

    # filepath: bpy.props.StringProperty(name=".dawarrangement file path", subtype='FILE_PATH', options={'SKIP_SAVE'})
    # filter_search: bpy.props.StringProperty(default="*.dawarrangement", options={'SKIP_SAVE'})
    # filter_glob: bpy.props.StringProperty(
    #     default="*.dawproject;*.als",
    #     options={'HIDDEN'},
    # )

    @classmethod
    def poll(cls, context):
        props = context.scene.audvis.daw_arrangement
        if props.filepath.lower().endswith(".dawproject"):
            return True
        elif props.filepath.lower().endswith(".als"):
            return True
        elif props.filepath.lower().endswith(supported_audio_extensions):
            return True
        return False

    #    def invoke(self, context, event):
    #        context.window_manager.fileselect_add(self)
    #        self.filter_search = '*.dawproject;*.als'
    #        return {'RUNNING_MODAL'}

    def execute(self, context):
        props: AudvisDawArrangement = context.scene.audvis.daw_arrangement
        if not props.filepath:
            return {'CANCELLED'}
        filepath = bpy.path.abspath(props.filepath)
        parsed_arrangement = None
        if filepath.lower().endswith(".dawproject"):
            parsed_arrangement = dawproject.parse(filepath, props)
        elif filepath.lower().endswith(".als"):
            parsed_arrangement = als.parse(filepath, props)
        elif filepath.lower().endswith(supported_audio_extensions):
            parsed_arrangement = audiofile.parse(filepath, props)
        # TODO: add other DAWs
        else:
            return {'CANCELLED'}
        self._import_data()
        if props.output == "geonodes1":
            from .outputs import geometrynodes1
            geometrynodes1.GeometryNodes1().make(context, parsed_arrangement)
        # elif props.output == "geonodes2":
        #    from .outputs import geometrynodes2
        #    geometrynodes2.GeometryNodes2().make(context, parsed_arrangement)
        # self._render(context, parsed_arrangement)
        return {'FINISHED'}

    def _import_data(self):
        if 'DawArrangement' not in bpy.data.node_groups:
            libpath = pathlib.Path(__file__).parent.resolve().__str__() + "/DawArrangement-blender3_6.blend"
            with bpy.data.libraries.load(libpath) as (data_from, data_to):
                data_to.materials = data_from.materials
                data_to.node_groups = data_from.node_groups
            bpy.data.libraries.remove(bpy.data.libraries[-1])


class AUDVIS_PT_DawprojectTo3d(AudVisButtonsPanel_Npanel):
    bl_label = "Import DAW Arrangement"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        props: AudvisDawArrangement = context.scene.audvis.daw_arrangement
        col = layout.column(align=True)
        col.prop(props, "filepath")
        col.prop(props, "frame_start")
        col.prop(props, "zoom")
        col.prop(props, "line_height")
        col.prop(props, "line_margin")
        col.prop(props, "clip_padding")
        col.prop(props, "thickness_clip")
        col.prop(props, "thickness_note")
        col = layout.column(align=True)
        col.prop(props, "track_name_position")
        col.prop(props, "track_name_bevel_depth")
        # col.prop(props, "output")
        col = layout.column(align=True)
        col.prop(props, "audio_curve_samplerate")
        col.prop(props, "audio_internal_samplerate")
        col.prop(props, "audio_algorithm")
        col.prop(props, "audio_amplitude")
        col = layout.column(align=True)
        row = col.row()
        row.prop(props, "replace_last_collection")
        row.prop(props, "last_collection")
        col.operator('audvis.dawarrangementto3d')


classes = [
    AUDVIS_OT_DawArrangementTo3D,
    AUDVIS_PT_DawprojectTo3d,
]
