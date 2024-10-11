import bpy
import sys
from bpy.types import (
    Operator,
)
from bpy_extras.io_utils import ImportHelper

from .. import midi_file_baker


class AUDVIS_OT_midiFileOpen(Operator, ImportHelper):
    bl_idname = "audvis.midi_file_open"
    bl_label = "Add Midi File"
    bl_description = ""

    filter_glob: bpy.props.StringProperty(
        default='*.mid;*.midi',
        options={'HIDDEN'}
    )

    strip_silent_start: bpy.props.BoolProperty(
        name="Strip Silent Beginning of MIDI",
        description="MIDI files use to have sometimes quite a long time from beginning to first note."
                    " This cuts that empty, silent part.",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return sys.modules['audvis'].audvis.is_midi_realtime_supported()

    def execute(self, context):
        midi_file_baker.bake(context.scene, self.filepath, self.strip_silent_start)

        return {'FINISHED'}
