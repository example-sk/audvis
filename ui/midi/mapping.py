"""MIDI Mappings: map knobs, faders and pads of a MIDI controller to any property in Blender
(AudVis or native) or to show actions (scene switching, Motion FX Engage / Release / Stop).

Right-click a value > AudVis: MIDI Learn > move a knob. Mappings are applied ~60x a second
from a timer, so they work while playing and while paused. Mappings of every scene are active.
"""
import ast
import re
import traceback
import uuid

import bpy
from bpy.types import Operator, UIList

from ...analyzer import midi_map
from ...switchscenes import switch_window_scene
from ...utils import midi_number_to_note
from ..buttonspanel import AudVisButtonsPanel_Npanel

TICK = 1 / 60
_states = {}  # mapping uid -> midi_map.MapState
_reported = set()
written = set()  # (ID pointer, data path, index) the mappings wrote - Map Mode ignores these changes
_PATH = re.compile(r'^bpy\.data\.(\w+)\[("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\]\.?(.*)$')
_ATTR = re.compile(r'^(?:(.*)\.)?(\w+)$')
_KEY = re.compile(r'^(.*)\[("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')\]$')
_INDEX = re.compile(r'^(.*)\[(\d+)\]$')
AXES = {'TRANSLATION', 'EULER', 'XYZ', 'XYZ_LENGTH', 'DIRECTION', 'VELOCITY', 'ACCELERATION', 'COORDINATES'}


# ---------------------------------------------------------------- targets

class Target:
    """A resolved property: owner struct + attribute (RNA) or key (custom property), array index."""

    def __init__(self, idb, owner, attr, key, index):
        self.idb, self.owner, self.attr, self.key, self.index = idb, owner, attr, key, index
        self.rna = owner.bl_rna.properties.get(attr) if attr is not None else None

    def _raw(self):
        value = getattr(self.owner, self.attr) if self.attr is not None else self.owner[self.key]
        return value[self.index] if self.index >= 0 else value

    def read(self):
        """Current value as a number (bool 0/1, enum: item index)."""
        value = self._raw()
        if self.rna is not None and self.rna.type == 'ENUM':
            return float([i.identifier for i in self.rna.enum_items].index(value))
        return float(value)

    def write(self, value):
        rna = self.rna
        if rna is not None and rna.type == 'ENUM':
            items = rna.enum_items
            value = items[max(0, min(len(items) - 1, round(value)))].identifier
        elif rna is not None and rna.type == 'BOOLEAN':
            value = value >= .5
        elif rna is not None and rna.type == 'INT':
            value = max(rna.hard_min, min(rna.hard_max, round(value)))
        elif rna is not None:
            value = max(rna.hard_min, min(rna.hard_max, value))
        else:  # custom property: keep its type
            value = type(self._raw())(round(value) if isinstance(self._raw(), int) else value)
        if self.index >= 0:
            if self.attr is not None:
                getattr(self.owner, self.attr)[self.index] = value
            else:
                self.owner[self.key][self.index] = value
        elif self.attr is not None:
            setattr(self.owner, self.attr, value)
        else:
            self.owner[self.key] = value

    def label(self):
        name = self.rna.name if self.rna is not None else self.key
        if self.index >= 0:
            subtype = self.rna.subtype if self.rna is not None else ''
            if subtype in AXES and self.index < 3:
                name += " " + "XYZ"[self.index]
            elif subtype.startswith('COLOR') and self.index < 4:
                name += " " + "RGBA"[self.index]
            else:
                name += " [{}]".format(self.index)
        return "{} > {}".format(self.idb.name, name)


def parse(full_path):
    """'bpy.data.objects["Cube"].location[2]' -> ('objects', 'Cube', 'location', 2)."""
    match = _PATH.match(full_path.strip())
    if match is None:
        raise ValueError("Not a bpy.data path - right-click the value > Copy Full Data Path")
    id_type, id_name, path = match.group(1), ast.literal_eval(match.group(2)), match.group(3)
    collection = getattr(bpy.data, id_type, None)
    idb = collection.get(id_name) if collection is not None else None
    if idb is None:
        raise ValueError("{} '{}' not found".format(id_type, id_name))
    index = -1
    indexed = _INDEX.match(path)
    if indexed is not None:
        try:
            container = idb.path_resolve(indexed.group(1))
        except ValueError:
            container = None
        if container is not None and not isinstance(container, (str, bpy.types.bpy_prop_collection)) \
                and hasattr(container, "__len__"):
            path, index = indexed.group(1), int(indexed.group(2))
    target = _target(idb, path, index)
    if target is None:
        raise ValueError("Can't resolve '{}'".format(path))
    if target.rna is not None and target.rna.type not in ('FLOAT', 'INT', 'BOOLEAN', 'ENUM') \
            or target.rna is not None and target.rna.is_enum_flag:
        raise ValueError("Only numbers, checkboxes and dropdowns can be mapped")
    if target.index < 0 and target.rna is not None and getattr(target.rna, "is_array", False):
        raise ValueError("Pick one component (e.g. Location X), not the whole vector")
    return id_type, id_name, path, index


def _target(idb, path, index):
    try:
        key = _KEY.match(path)
        if key is not None:
            owner = idb.path_resolve(key.group(1)) if key.group(1) else idb
            target = Target(idb, owner, None, ast.literal_eval(key.group(2)), index)
        else:
            attr = _ATTR.match(path)
            if attr is None:
                return None
            owner = idb.path_resolve(attr.group(1)) if attr.group(1) else idb
            target = Target(idb, owner, attr.group(2), None, index)
        target.read()
        return target
    except (ValueError, KeyError, IndexError, AttributeError, TypeError):
        return None


def resolve(m):
    collection = getattr(bpy.data, m.id_type, None) if m.id_type else None
    idb = collection.get(m.id_name) if collection is not None else None
    return _target(idb, m.data_path, m.index) if idb is not None else None


def default_range(target):
    rna = target.rna
    current = target.read()
    if rna is None:
        return (0.0, 1.0) if 0 <= current <= 1 else (current - 1, current + 1)
    if rna.type == 'BOOLEAN':
        return 0.0, 1.0
    if rna.type == 'ENUM':
        return 0.0, float(len(rna.enum_items) - 1)
    lo, hi = rna.soft_min, rna.soft_max
    lo = lo if abs(lo) <= 1e4 else current - 1
    hi = hi if abs(hi) <= 1e4 else (max(current * 2, lo + 1) if lo >= 0 else current + 1)
    return float(lo), float(hi)


def status(m):
    """None, or (icon, text) explaining why a mapping may not act as expected."""
    if m.target == 'action':
        return None
    target = resolve(m)
    if target is None:
        return 'ERROR', "Target not found (renamed or deleted?)"
    anim = target.idb.animation_data if hasattr(target.idb, "animation_data") else None
    if anim is not None:
        index = max(0, m.index)
        if any(d.data_path == m.data_path and d.array_index == index for d in anim.drivers):
            return 'DRIVER', "Has a driver - the driver wins"
        from ...utils import action_get_fcurves
        if anim.action is not None and any(fc.data_path == m.data_path and fc.array_index == index
                                           for fc in action_get_fcurves(anim.action)):
            return 'KEYFRAME', "Keyframed - the keyframes win on the next frame (turn on Record)"
    return None


def source_label(m):
    if m.kind == 'cc':
        text = "CC {}".format(m.number)
    else:
        text = "{} ({})".format(midi_number_to_note(m.number) or m.number, m.number)
    return text + (" ch{}".format(m.channel) if m.channel else "")


def target_label(m):
    if m.target == 'action':
        label = m.bl_rna.properties['action'].enum_items[m.action].name
        return label + (": " + m.scene_name if m.action == 'scene' else "")
    target = resolve(m)
    return target.label() if target is not None else (m.full_path or "Paste a data path")


# ---------------------------------------------------------------- mappings

def forget(m):
    _states.pop(m.uid, None)


def on_path_update(m, context):
    """Data Path pasted / learned: split it up and set a sensible range."""
    if not m.full_path:
        return
    try:
        m.id_type, m.id_name, m.data_path, m.index = parse(m.full_path)
    except ValueError:
        m.id_type = m.id_name = m.data_path = ""
        return
    target = resolve(m)
    m.range_min, m.range_max = default_range(target)
    if target.rna is not None and target.rna.type == 'BOOLEAN' and m.kind == 'note':
        m.response = 'toggle'
    forget(m)


def create(scene, kind, number, channel=0, device="", full_path="", action=None):
    """New mapping in scene (property via full_path, or an action)."""
    maps = scene.audvis.midi_realtime.maps
    m = maps.add()
    m.uid = uuid.uuid4().hex
    m.kind, m.number, m.channel, m.device = kind, number, channel, device
    m.response = 'range' if kind == 'cc' else 'momentary'
    if action is not None:
        m.target, m.action = 'action', action
    else:
        m.full_path = full_path  # parses and sets the range
    scene.audvis.midi_realtime.maps_index = len(maps) - 1
    return m


def _window():
    wm = bpy.context.window_manager
    return wm.windows[0] if wm is not None and len(wm.windows) else None


def run_action(m):
    window = _window()
    if window is None:
        return
    if m.action == 'play':
        with bpy.context.temp_override(window=window, screen=window.screen):
            bpy.ops.screen.animation_play()
    elif m.action in ('next_scene', 'prev_scene', 'scene'):
        scenes = list(bpy.data.scenes)
        if m.action == 'scene':
            scene = bpy.data.scenes.get(m.scene_name)
        else:
            i = scenes.index(window.scene) + (1 if m.action == 'next_scene' else -1)
            scene = scenes[i % len(scenes)]
        if scene is not None and scene != window.scene:
            switch_window_scene(window, scene)
    else:
        with bpy.context.temp_override(window=window):
            bpy.ops.audvis.motion_fade(action=m.action, effect='all', object_name="")


def apply(snapshot, analyzer, playing):
    """Apply every enabled mapping of every scene once. Returns True if anything changed."""
    changed = False
    for scene in bpy.data.scenes:
        for m in scene.audvis.midi_realtime.maps:
            if not m.enable or not m.uid:
                continue
            state = _states.get(m.uid)
            if state is None:
                state = _states[m.uid] = midi_map.MapState()
            device = analyzer.device_key(m.device) if m.device else None
            raw, held, presses = midi_map.lookup(snapshot, m.kind, m.number, m.channel, device)
            if m.target == 'action':
                if midi_map.presses(m, state, held, presses):
                    run_action(m)
                    changed = True
                continue
            target = resolve(m)
            if target is None:
                continue
            current = target.read()
            value = midi_map.step(m, state, raw, held, presses, current)
            if value is None:
                continue
            target.write(value)
            state.written = target.read()
            written.add((target.idb.as_pointer(), m.data_path, m.index))
            changed = True
            if m.record and playing:
                target.idb.keyframe_insert(m.data_path, index=m.index, frame=scene.frame_current)
    return changed


def _tick():
    try:
        scene = bpy.context.scene
        audvis = getattr(bpy, "audvis", None)
        if audvis is None or scene is None or not scene.audvis.midi_realtime.enable:
            return .25
        analyzer = audvis.get_midi_realtime_analyzer(scene)
        if analyzer is None:
            return .25
        analyzer.on_pre_frame(scene, scene.frame_current_final)  # opens devices, fresh values while paused
        snapshot = analyzer.snapshot()
        if snapshot is None:
            return TICK
        wm = bpy.context.window_manager
        playing = any(w.screen.is_animation_playing for w in wm.windows) if wm is not None else False
        if apply(snapshot, analyzer, playing) and wm is not None:
            for window in wm.windows:  # live values in the sidebar
                for area in window.screen.areas:
                    for region in area.regions:
                        if region.type == 'UI':
                            region.tag_redraw()
    except Exception:
        key = traceback.format_exc().splitlines()[-1]
        if key not in _reported:  # don't flood the console 60x a second
            _reported.add(key)
            print("AudVis MIDI Mappings:")
            traceback.print_exc()
    return TICK


# ---------------------------------------------------------------- operators

def full_path_of(idb, path, index=-1):
    """bpy.data path of a property: (ID, path from the ID, array index) -> 'bpy.data.objects["Cube"].location[2]'."""
    if idb is None or not path:
        return ""
    base = repr(idb)  # bpy.data.objects['Cube'] (embedded data: bpy.data.materials['M'].node_tree)
    if not base.startswith("bpy.data."):
        return ""
    full = base + ("" if path.startswith("[") else ".") + path
    return full + ("[{}]".format(index) if index is not None and index >= 0 else "")


def hovered_path(context):
    """Full data path of the value under the mouse / right-clicked, or ""."""
    prop = getattr(context, "property", None)  # (ID, path, index) of the hovered button
    if prop:
        idb, path, index = prop
        full = full_path_of(idb, path, index)
        if full:
            return full
    pointer, rna = getattr(context, "button_pointer", None), getattr(context, "button_prop", None)
    if pointer is not None and rna is not None and pointer.id_data is not None:
        try:
            path = pointer.path_from_id(rna.identifier)
        except ValueError:
            path = ""
        full = full_path_of(pointer.id_data, path)
        if full and not getattr(rna, "is_array", False):
            return full
    wm = context.window_manager  # last resort: what Copy Full Data Path would copy
    old = wm.clipboard
    try:
        bpy.ops.ui.copy_data_path_button(full_path=True)
        return wm.clipboard if wm.clipboard != old else ""
    except RuntimeError:
        return ""
    finally:
        wm.clipboard = old


class AUDVIS_OT_midiMapLearn(Operator):
    """Move a knob, fader or pad on your MIDI controller to map it (Esc cancels)"""
    bl_idname = "audvis.midi_map_learn"
    bl_label = "AudVis: MIDI Learn"

    full_path: bpy.props.StringProperty(options={'SKIP_SAVE'})
    map_index: bpy.props.IntProperty(default=-1, options={'SKIP_SAVE'},
                                     description="Re-learn the knob of this mapping. -1 = new mapping")
    action: bpy.props.StringProperty(options={'SKIP_SAVE'}, description="New action mapping")

    _timer = None
    _start_msg = None
    _scene_name = ""

    @staticmethod
    def _analyzer(scene):
        if not scene.audvis.midi_realtime.enable:
            return None
        return bpy.audvis.get_midi_realtime_analyzer(scene)

    def invoke(self, context, event):
        scene = context.scene
        if self.map_index < 0 and not self.action:
            if not self.full_path:
                self.full_path = hovered_path(context)
            try:
                parse(self.full_path)
            except ValueError as e:
                self.report({'ERROR'}, str(e))
                return {'CANCELLED'}
        analyzer = self._analyzer(scene)
        if analyzer is None:
            self.report({'ERROR'}, "Enable MIDI Realtime (AudVis sidebar) and add your controller first")
            return {'CANCELLED'}
        self._scene_name = scene.name
        self._start_msg = analyzer.get_last_msg()
        self._timer = context.window_manager.event_timer_add(.05, window=context.window)
        context.window_manager.modal_handler_add(self)
        context.workspace.status_text_set("AudVis: move a knob / fader or hit a pad to map it (Esc cancels)")
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        context.window_manager.event_timer_remove(self._timer)
        if context.workspace is not None:
            context.workspace.status_text_set(None)

    def modal(self, context, event):
        scene = bpy.data.scenes.get(self._scene_name)
        if scene is None or event.type == 'ESC':
            self._finish(context)
            return {'CANCELLED'}
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        analyzer = self._analyzer(scene)
        if analyzer is None:
            self.report({'WARNING'}, "MIDI Realtime stopped - learn cancelled")
            self._finish(context)
            return {'CANCELLED'}
        msg = analyzer.get_last_msg()
        if msg is None or msg is self._start_msg or (not hasattr(msg, "control") and not msg.on):
            return {'PASS_THROUGH'}
        kind = 'cc' if hasattr(msg, "control") else 'note'
        number = msg.control if kind == 'cc' else msg.note
        maps = scene.audvis.midi_realtime.maps
        if 0 <= self.map_index < len(maps):
            m = maps[self.map_index]
            m.kind, m.number, m.channel, m.device = kind, number, msg.channel, ""
            forget(m)
        else:
            m = create(scene, kind, number, msg.channel, full_path=self.full_path,
                       action=self.action or None)
        self.report({'INFO'}, "{} > {}".format(source_label(m), target_label(m)))
        self._finish(context)
        return {'FINISHED'}


class AUDVIS_OT_midiMapAdd(Operator):
    """Add a mapping - paste a data path, or pick an action"""
    bl_idname = "audvis.midi_map_add"
    bl_label = "Add MIDI Mapping"
    bl_options = {'UNDO'}

    target: bpy.props.EnumProperty(items=[('property', "Property", ""), ('action', "Action", "")])

    def execute(self, context):
        m = create(context.scene, 'cc', 1, action='play' if self.target == 'action' else None)
        if self.target == 'action':
            m.kind, m.response = 'note', 'momentary'
        return {'FINISHED'}


class AUDVIS_OT_midiMapRemove(Operator):
    """Remove the selected mapping"""
    bl_idname = "audvis.midi_map_remove"
    bl_label = "Remove MIDI Mapping"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.audvis.midi_realtime
        return 0 <= props.maps_index < len(props.maps)

    def execute(self, context):
        props = context.scene.audvis.midi_realtime
        forget(props.maps[props.maps_index])
        props.maps.remove(props.maps_index)
        props.maps_index = min(props.maps_index, len(props.maps) - 1)
        return {'FINISHED'}


def draw_context_menu(self, context):
    if getattr(context, "button_prop", None) is None:
        return
    layout = self.layout
    layout.separator()
    layout.operator("audvis.midi_map_learn", icon='EVENT_M')


# ---------------------------------------------------------------- UI

class AUDVIS_UL_midiMaps(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "enable", text="")
        sub = row.split(factor=.3, align=True)
        sub.label(text=source_label(item))
        problem = status(item)
        sub.label(text=target_label(item), icon=problem[0] if problem else
                  ('PLAY' if item.target == 'action' else 'RNA'))


class AUDVIS_PT_midiMapsNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "MIDI Mappings"
    bl_parent_id = "AUDVIS_PT_midiRealtimeNpanel"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        props = context.scene.audvis.midi_realtime
        if not props.enable:
            layout.label(text="Enable MIDI Realtime above", icon='INFO')
        from . import map_mode
        map_mode.draw_button(layout, context)
        row = layout.row()
        row.template_list("AUDVIS_UL_midiMaps", "", props, "maps", props, "maps_index", rows=4)
        col = row.column(align=True)
        col.operator("audvis.midi_map_add", text="", icon='ADD').target = 'property'
        col.operator("audvis.midi_map_add", text="", icon='PLAY').target = 'action'
        col.operator("audvis.midi_map_remove", text="", icon='REMOVE')
        if not 0 <= props.maps_index < len(props.maps):
            return
        m = props.maps[props.maps_index]
        index = props.maps_index

        box = layout.box().column(align=True)
        row = box.row(align=True)
        row.prop(m, "kind", text="")
        row.prop(m, "number", text="")
        row.prop(m, "channel", text="Ch")
        row.operator("audvis.midi_map_learn", text="", icon='EYEDROPPER').map_index = index
        box.prop(m, "device", icon='PLUGIN')
        state = _states.get(m.uid)
        if state is not None and state.raw is not None:
            box.progress(factor=state.raw, type='BAR', text="Input {:.0f}%".format(state.raw * 100))

        box = layout.box().column(align=True)
        box.row().prop(m, "target", expand=True)
        if m.target == 'action':
            box.prop(m, "action", text="")
            if m.action == 'scene':
                box.prop_search(m, "scene_name", bpy.data, "scenes")
            return
        box.prop(m, "full_path", text="")
        box.label(text=target_label(m))
        problem = status(m)
        if problem:
            row = box.row()
            row.alert = problem[0] == 'ERROR'
            row.label(text=problem[1], icon=problem[0])

        col = layout.column(align=True)
        col.prop(m, "response")
        row = col.row(align=True)
        row.prop(m, "range_min")
        row.prop(m, "range_max")
        if m.response == 'range':
            row = col.row(align=True)
            row.prop(m, "curve")
            row.prop(m, "invert", toggle=True)
            col.prop(m, "smoothing", slider=True)
            col.prop(m, "pickup")
        col.prop(m, "record")


def register():
    bpy.types.UI_MT_button_context_menu.append(draw_context_menu)
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=.5, persistent=True)


def unregister():
    bpy.types.UI_MT_button_context_menu.remove(draw_context_menu)
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
    _states.clear()


classes = [
    AUDVIS_OT_midiMapLearn,
    AUDVIS_OT_midiMapAdd,
    AUDVIS_OT_midiMapRemove,
    AUDVIS_UL_midiMaps,
    AUDVIS_PT_midiMapsNpanel,
]
