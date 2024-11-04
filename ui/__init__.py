import bpy

from . import (
    realtime,
    generator,
    sequence,
    partymode,
    scripttemplates,
    force_reload,
    values,
    video,
    shapemodifier,
    global_settings,
    drivers_bake,
    spectrogram,
    animation_nodes,
    preferences,
    armature_generator,
    install_ui,
    props,
    midi,
    spread_drivers,
    bge,
    dawscene
)
from .buttonspanel import AudVisButtonsPanel_Npanel


class AUDVIS_PT_audvisNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "AudVis - Audio Visualizer"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Sync Mode:")
        row.prop(context.scene, "sync_mode", text="", text_ctxt="Set AV-sync if your sound is out of sync while playing")

        col = layout.column(align=True)
        col.prop(context.scene.audvis, "sample")
        col.prop(context.scene.audvis, "subframes")
        col.prop(context.scene.audvis, "channels")
        col.prop(context.scene.audvis, "default_channel_sound")
        row = col.row()
        row.label(text="Default MIDI Channel")
        row.prop(context.scene.audvis, "default_channel_midi", text="")

        col = layout.column(align=True)
        col.operator("audvis.forcereload", text="Reload AudVis", icon='FILE_REFRESH')


class AUDVIS_OT_copyString(bpy.types.Operator):
    bl_idname = "audvis.copy_string"
    bl_label = "Copy to Clipboard"

    value: bpy.props.StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.value
        return {"FINISHED"}


class AudvisWindowProperties(bpy.types.PropertyGroup):
    ispartymode: bpy.props.BoolProperty(name="Is Party Mode Window", default=False)


def register():
    scripttemplates.register()
    partymode.register()
    spread_drivers.register()
    bpy.types.Scene.audvis = bpy.props.PointerProperty(type=props.scene.AudvisSceneProperties)
    bpy.types.Object.audvis = bpy.props.PointerProperty(type=props.obj.AudvisObjectProperties)
    bpy.types.SoundSequence.audvis = bpy.props.PointerProperty(type=props.sequence.AudvisSequenceProperties)
    bpy.types.Window.audvis = bpy.props.PointerProperty(type=AudvisWindowProperties)
    preferences.on_npanelname_update(bpy.context.preferences.addons[bpy.audvis._module_name].preferences, bpy.context)


def unregister():
    scripttemplates.unregister()
    partymode.unregister()
    spread_drivers.unregister()
    realtime.unregister()
    video.unregister()
    del bpy.types.Scene.audvis
    del bpy.types.Object.audvis
    del bpy.types.SoundSequence.audvis
    del bpy.types.Window.audvis


def on_blendfile_loaded():
    video.on_blendfile_loaded()


def on_blendfile_save():
    video.on_blendfile_save()


classes = [
              AUDVIS_OT_copyString,
              AUDVIS_PT_audvisNpanel,
              AudvisWindowProperties,
          ] \
          + props.classes \
          + values.classes \
          + sequence.classes \
          + realtime.classes \
          + midi.classes \
          + partymode.classes \
          + video.classes \
          + shapemodifier.classes \
          + armature_generator.classes \
          + generator.classes \
          + scripttemplates.classes \
          + force_reload.classes \
          + spectrogram.classes \
          + drivers_bake.classes \
          + animation_nodes.classes \
          + spread_drivers.classes \
          + install_ui.classes \
          + preferences.classes \
          + bge.classes \
          + dawscene.classes \
          + []
