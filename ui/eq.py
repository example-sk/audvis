"""EQ / Macros: eight shared frequency bands Motion FX can opt into, each with a gain
slider that a MIDI knob / fader can be mapped to, and live level meters."""
import time

import bpy

from ..analyzer.motion.audio import EQ_EDGES, eq_gain
from .buttonspanel import AudVisButtonsPanel_Npanel

BAND_COUNT = 8

_levels = {}  # (scene name, band index) -> 0..1, kept out of RNA so the meters don't dirty the file
_learning = None  # (scene name, band index) while Map waits for a knob


def bands(scene):
    return [getattr(scene.audvis, 'eq_band_%d' % i) for i in range(1, BAND_COUNT + 1)]


def _tag_redraw(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in {'VIEW_3D', 'PROPERTIES'}:
                area.tag_redraw()


class AUDVIS_OT_eqMap(bpy.types.Operator):
    """Click, then move a MIDI knob or fader to control this band's gain (Esc cancels)"""
    bl_idname = 'audvis.eq_map'
    bl_label = 'Map EQ Gain'

    band: bpy.props.IntProperty(min=1, max=BAND_COUNT, default=1)

    _timer = None
    _start_msg = None
    _started = 0.0
    _scene_name = ""

    @classmethod
    def poll(cls, context):
        return context.scene.audvis.midi_realtime.enable

    @staticmethod
    def _analyzer(scene):
        if not scene.audvis.midi_realtime.enable:
            return None
        return bpy.audvis.get_midi_realtime_analyzer(scene)

    def invoke(self, context, event):
        global _learning
        analyzer = self._analyzer(context.scene)
        if analyzer is None:
            self.report({'ERROR'}, "Enable MIDI Realtime first")
            return {'CANCELLED'}
        self._scene_name = context.scene.name
        self._start_msg = analyzer.get_last_msg()
        self._started = time.monotonic()
        self._timer = context.window_manager.event_timer_add(.05, window=context.window)
        context.window_manager.modal_handler_add(self)
        _learning = (self._scene_name, self.band - 1)
        context.workspace.status_text_set("AudVis: move a MIDI knob to map band {} (Esc cancels)".format(self.band))
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        global _learning
        _learning = None
        context.window_manager.event_timer_remove(self._timer)
        if context.workspace is not None:
            context.workspace.status_text_set(None)
        _tag_redraw(context)

    def modal(self, context, event):
        scene = bpy.data.scenes.get(self._scene_name)
        if scene is None or event.type == 'ESC' or time.monotonic() - self._started > 15:
            self._finish(context)
            return {'CANCELLED'}
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        analyzer = self._analyzer(scene)
        if analyzer is None:  # MIDI Realtime switched off / AudVis reloaded while waiting
            self.report({'WARNING'}, "MIDI Realtime stopped - mapping cancelled")
            self._finish(context)
            return {'CANCELLED'}
        msg = analyzer.get_last_msg()
        if msg is not None and msg is not self._start_msg and hasattr(msg, 'control'):
            band = bands(scene)[self.band - 1]
            band.control = msg.control
            band.channel = msg.channel
            band.mapped = True
            self.report({'INFO'}, "Band {}: CC {} (channel {})".format(self.band, msg.control, msg.channel))
            self._finish(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}


class AUDVIS_OT_eqUnmap(bpy.types.Operator):
    """Stop controlling this band's gain by MIDI"""
    bl_idname = 'audvis.eq_unmap'
    bl_label = 'Clear MIDI Mapping'
    bl_options = {'UNDO'}

    band: bpy.props.IntProperty(min=1, max=BAND_COUNT, default=1)

    def execute(self, context):
        bands(context.scene)[self.band - 1].mapped = False
        return {'FINISHED'}


class AUDVIS_OT_eqWindow(bpy.types.Operator):
    """Open the EQ / Macros panel in its own window"""
    bl_idname = 'audvis.eq_window'
    bl_label = 'Open EQ Window'

    def execute(self, context):
        before = {w.as_pointer() for w in context.window_manager.windows}
        area = context.area or context.screen.areas[0]
        # area_dupli gives a window with just one area; window_new copies the whole layout
        with context.temp_override(area=area):
            bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
        window = next((w for w in context.window_manager.windows if w.as_pointer() not in before), None)
        if window is None:
            self.report({'ERROR'}, "Could not open a new window")
            return {'CANCELLED'}
        window.audvis.iseq = True
        area = window.screen.areas[0]
        area.type = 'PROPERTIES'
        area.spaces.active.context = 'SCENE'
        return {'FINISHED'}


def draw_eq(layout, context):
    scene = context.scene
    row = layout.row(align=True)
    row.prop(scene.audvis, 'eq_channel')
    if not context.window.audvis.iseq:
        row.operator('audvis.eq_window', text="", icon='WINDOW')
    grid = layout.grid_flow(row_major=True, columns=4, even_columns=True, align=True)
    for i, band in enumerate(bands(scene)):
        col = grid.box().column(align=True)
        col.label(text="{:g}-{:g} Hz".format(EQ_EDGES[i], EQ_EDGES[i + 1]))
        col.progress(factor=_levels.get((scene.name, i), 0.0), type='BAR', text="Band {}".format(i + 1))
        sub = col.column(align=True)
        sub.enabled = not band.mapped  # the knob owns the gain while mapped
        sub.prop(band, 'gain', slider=True)
        row = col.row(align=True)
        if _learning == (scene.name, i):
            row.label(text="Move a knob...", icon='REC')
        else:
            row.operator('audvis.eq_map', text="Map", icon='EYEDROPPER').band = i + 1
        if band.mapped:
            row.operator('audvis.eq_unmap', text="", icon='X').band = i + 1
            row = col.row(align=True)
            row.prop(band, 'control', text="CC")
            row.prop(band, 'channel', text="Ch")
    if not scene.audvis.midi_realtime.enable:
        layout.label(text="Enable MIDI Realtime to map knobs", icon='INFO')
    layout.label(text="Pick a band in a Motion FX Sound section", icon='INFO')


class AUDVIS_PT_eq(AudVisButtonsPanel_Npanel):
    bl_label = "EQ / Macros"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        draw_eq(self.layout, context)


class AUDVIS_PT_eqWindow(bpy.types.Panel):
    bl_label = "AudVis EQ / Macros"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'scene'

    @classmethod
    def poll(cls, context):
        return context.window is not None and context.window.audvis.iseq

    def draw(self, context):
        draw_eq(self.layout, context)


def update_meters():
    try:
        context = bpy.context
        if context.window_manager is None or not hasattr(bpy, 'audvis'):
            return .5
        scene = context.scene  # audvis.driver() reads bpy.context.scene too
        engine = bpy.audvis._get_motion_engine()
        changed = False
        for i, band in enumerate(bands(scene)):
            try:
                value = bpy.audvis.driver(EQ_EDGES[i], EQ_EDGES[i + 1], ch=scene.audvis.eq_channel)
                level = min(1.0, max(0.0, value * .1 * eq_gain(band, engine.cc_reader)))
            except Exception:
                level = 0.0
            key = (scene.name, i)
            if abs(_levels.get(key, 0.0) - level) > .005:
                _levels[key] = level
                changed = True
        if changed:  # silence doesn't redraw every tick
            _tag_redraw(context)
    except Exception:
        pass  # never let the timer die
    return .1


def register():
    if not bpy.app.timers.is_registered(update_meters):
        bpy.app.timers.register(update_meters, first_interval=.1, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(update_meters):
        bpy.app.timers.unregister(update_meters)
    _levels.clear()


classes = [
    AUDVIS_OT_eqMap,
    AUDVIS_OT_eqUnmap,
    AUDVIS_OT_eqWindow,
    AUDVIS_PT_eq,
    AUDVIS_PT_eqWindow,
]
