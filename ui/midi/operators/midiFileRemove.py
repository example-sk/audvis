import sys

from bpy.types import (
    Operator,
)
import bpy

from ..utils import get_selected_midi_file


class AUDVIS_OT_midiFileRemove(Operator):
    bl_idname = "audvis.midi_file_remove"
    bl_label = "Remove Midi File"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        if not sys.modules['audvis'].audvis.is_midi_realtime_supported():
            return False
        if get_selected_midi_file(context) is None:
            return False
        return True

    def execute(self, context):
        midifile = get_selected_midi_file(context)
        if midifile is not None \
                and context.scene.animation_data \
                and context.scene.animation_data.action is not None:
            fcurves = context.scene.animation_data.action.fcurves
            for fcurve in fcurves:
                if fcurve.data_path.startswith(midifile.path_from_id()):
                    fcurves.remove(fcurve)
            midifile.deleted = True
            midifile.enable = False
            midifile.name = '_deleted'
            midifile.filepath = ''
            midifile.tracks.clear()
            # TODO: try to really delete? Check if fcurves work how expected
        return {'FINISHED'}
