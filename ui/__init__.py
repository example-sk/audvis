import colorsys
import zlib

import bpy
import bpy.utils.previews

from ..switchscenes import switch_window_scene
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
    motion,
    eq,
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
    daw_arrangement
)
from .buttonspanel import AudVisButtonsPanel_Npanel


class AUDVIS_PT_audvisNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "AudVis - Audio Visualizer"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout

        # Quick scene launcher. A grid keeps this useful for projects with a
        # handful of scenes without taking over the rest of the AudVis panel.
        box = layout.box()
        box.label(text="Scenes", icon='SCENE_DATA')
        grid = box.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
        grid.scale_y = 1.4
        for scene in bpy.data.scenes:
            op = grid.operator("audvis.scene_select", text=scene.name,
                               icon_value=_scene_icon_id(scene.name),
                               depress=context.window.scene == scene)
            op.scene_name = scene.name

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


# Color swatch icons for the scene launcher. Blender's UI API can't tint a
# button or its text, so each button gets a solid-colored icon instead.
_scene_icons = None


def _scene_color(name):
    # Seeded by the scene name (crc32, not the per-session salted hash()) so a
    # scene keeps its color across sessions while performing. Saturation and
    # value also vary so two scenes with similar hues still look different.
    seed = zlib.crc32(name.encode("utf-8"))
    hue = (seed & 0xFFFF) / 0xFFFF
    saturation = 0.6 + 0.4 * (((seed >> 16) & 0xFF) / 0xFF)
    value = 0.75 + 0.25 * (((seed >> 24) & 0xFF) / 0xFF)
    return colorsys.hsv_to_rgb(hue, saturation, value)


def _scene_icon_id(name):
    global _scene_icons
    if _scene_icons is None:
        _scene_icons = bpy.utils.previews.new()
    preview = _scene_icons.get(name)
    if preview is None:
        preview = _scene_icons.new(name)
        size = 32
        preview.icon_size = (size, size)
        preview.icon_pixels_float = (*_scene_color(name), 1.0) * (size * size)
    return preview.icon_id


class AUDVIS_OT_copyString(bpy.types.Operator):
    bl_idname = "audvis.copy_string"
    bl_label = "Copy to Clipboard"

    value: bpy.props.StringProperty()

    def execute(self, context):
        context.window_manager.clipboard = self.value
        return {"FINISHED"}


class AUDVIS_OT_scene_select(bpy.types.Operator):
    """Switch the active window to a project scene from the AudVis grid."""

    bl_idname = "audvis.scene_select"
    bl_label = "Switch Scene"

    scene_name: bpy.props.StringProperty(name="Scene")

    def execute(self, context):
        scene = bpy.data.scenes.get(self.scene_name)
        if scene is None:
            self.report({'WARNING'}, "Scene no longer exists")
            return {'CANCELLED'}
        switch_window_scene(context.window, scene)
        return {'FINISHED'}


class AudvisWindowProperties(bpy.types.PropertyGroup):
    ispartymode: bpy.props.BoolProperty(name="Is Party Mode Window", default=False)
    iseq: bpy.props.BoolProperty(name="Is EQ Window", default=False)


def register():
    scripttemplates.register()
    partymode.register()
    spread_drivers.register()
    eq.register()
    midi.register()
    bpy.types.Scene.audvis = bpy.props.PointerProperty(type=props.scene.AudvisSceneProperties)
    bpy.types.Object.audvis = bpy.props.PointerProperty(type=props.obj.AudvisObjectProperties)
    if hasattr(bpy.types, "SoundSequence"):
        bpy.types.SoundSequence.audvis = bpy.props.PointerProperty(type=props.sequence.AudvisSequenceProperties)
    else:
        bpy.types.SoundStrip.audvis = bpy.props.PointerProperty(type=props.sequence.AudvisSequenceProperties)
    bpy.types.Window.audvis = bpy.props.PointerProperty(type=AudvisWindowProperties)
    preferences.on_npanelname_update(bpy.context.preferences.addons[bpy.audvis._module_name].preferences, bpy.context)


def unregister():
    global _scene_icons
    if _scene_icons is not None:
        bpy.utils.previews.remove(_scene_icons)
        _scene_icons = None
    scripttemplates.unregister()
    partymode.unregister()
    spread_drivers.unregister()
    eq.unregister()
    midi.unregister()
    motion.unregister()
    realtime.unregister()
    video.unregister()
    del bpy.types.Scene.audvis
    del bpy.types.Object.audvis
    if hasattr(bpy.types, "SoundSequence"):
        del bpy.types.SoundSequence.audvis
    else:
        del bpy.types.SoundStrip.audvis
    del bpy.types.Window.audvis


def on_blendfile_loaded():
    video.on_blendfile_loaded()


def on_blendfile_save():
    video.on_blendfile_save()


classes = [
              AUDVIS_OT_copyString,
              AUDVIS_OT_scene_select,
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
          + motion.classes \
          + eq.classes \
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
          + daw_arrangement.classes \
          + []
