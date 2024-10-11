import sys

from bpy.types import (
    Operator,
)
import bpy

from ..utils import get_selected_midi_track


class AUDVIS_OT_midiTrackRemove(Operator):
    bl_idname = "audvis.midi_track_remove"
    bl_label = "Remove Midi Track"
    bl_description = ""

    @classmethod
    def poll(cls, context):
        if not bpy.audvis.is_midi_realtime_supported():
            return False
        if get_selected_midi_track(context) is None:
            return False
        return True

    def execute(self, context):
        track = get_selected_midi_track(context)
        if track is not None \
                and context.scene.animation_data \
                and context.scene.animation_data.action is not None:
            fcurves = context.scene.animation_data.action.fcurves
            for fcurve in fcurves:
                if fcurve.data_path.startswith(track.path_from_id()):
                    fcurves.remove(fcurve)
            track.deleted = True
            track.enable = False
            track.name = '_deleted'
            # TODO: try to really delete? Check if fcurves work how expected
        return {'FINISHED'}
