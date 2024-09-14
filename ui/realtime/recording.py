import math
import sys

import bpy

from ..buttonspanel import AudVisButtonsPanel_Npanel


def _get_audvis():
    return bpy.audvis


def _poll():
    audvis = _get_audvis()
    if audvis.realtime_analyzer is None:
        return False
    if audvis.realtime_analyzer.recorder is None:
        return False
    if audvis.realtime_analyzer.recorder.status == audvis.realtime_analyzer.recorder.STATUS_RUNNING:
        return True
    return False


class AUDVIS_OT_RealtimeRecordStart(bpy.types.Operator):
    bl_idname = "audvis.realtime_record_start"
    bl_label = "Start recording sound from sound card"
    bl_description = "Enable realtime analyzer to make this work"

    @classmethod
    def poll(cls, context):
        return context.scene.audvis.realtime_enable and not _poll()

    def execute(self, context):
        audvis = _get_audvis()
        audvis.update_data(context.scene)
        audvis.realtime_analyzer.recorder.start()
        return {'FINISHED'}


class AUDVIS_OT_RealtimeRecordStop(bpy.types.Operator):
    bl_idname = "audvis.realtime_record_stop"
    bl_label = "Stop recording sound from sound card"

    @classmethod
    def poll(cls, context):
        return _poll()

    def execute(self, context):
        audvis = _get_audvis()
        path = audvis.realtime_analyzer.recorder_stop(bpy.app.tempdir, context.scene.audvis.realtime_save_format)
        if context.scene.audvis.realtime_loadassequence:
            context.scene.sequence_editor_create()  # ensure sequence_editor exists
            sequence = context.scene.sequence_editor.sequences.new_sound(name="AudVis Record", filepath=path, channel=1,
                                                                         frame_start=context.scene.frame_start)
            if context.scene.audvis.realtime_save_pack:
                sequence.sound.pack()
        return {'FINISHED'}


def get_available_formats(self, context):
    # TODO: cache
    try:
        import soundfile
        lst = []
        formats = soundfile.available_formats()
        for key in formats:
            lst.append((key, formats[key], key))
        return lst
    except:
        return []


class AUDVIS_PT_realtimeRecordNpanel(AudVisButtonsPanel_Npanel):
    bl_parent_id = "AUDVIS_PT_realtimeNpanel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_label = "Record Audio"

    @classmethod
    def poll(cls, context):
        return bpy.audvis.is_realtime_supported()

    def draw(self, context):
        col = self.layout.column(align=True)
        if bpy.audvis.is_recording_supported():
            if bpy.audvis.realtime_analyzer is None:
                # bpy.audvis.update_data(context.scene) # wrong context
                pass
            try:
                seconds = bpy.audvis.realtime_analyzer.recorder.seconds
            except:
                seconds = 0
            minutes = math.floor(seconds / 60)
            col.prop(context.scene.audvis, 'realtime_save_format')
            col.prop(context.scene.audvis, 'realtime_loadassequence')
            if context.scene.audvis.realtime_loadassequence:
                col.prop(context.scene.audvis, 'realtime_save_pack')
            col.operator("audvis.realtime_record_start", text="start recording")
            col.operator("audvis.realtime_record_stop", text="stop recording")
            col.label(text="Recorded: %02d:%02d" % (minutes, math.floor(seconds - minutes * 60)))
        else:
            col.operator("audvis.install", text="Install python packages")


classes = [
    AUDVIS_OT_RealtimeRecordStart,
    AUDVIS_OT_RealtimeRecordStop,
    AUDVIS_PT_realtimeRecordNpanel,
]
