"""Map Mode: switch it on, click (or change) any value in Blender, move a knob / fader / pad - mapped.
Repeat for as many values as you like; Esc or the button again switches it off.

A value is armed two ways, so it works anywhere in the UI:
- the button under the mouse when you click (Blender's `context.property`, read in the region under the mouse)
- any value you change: IDs updated by the depsgraph are compared with a snapshot of their properties
"""
import time

import bpy
from bpy.types import Operator

from . import mapping
from ...analyzer.motion.lib import HELPER_KEY, INDEX_KEY

_SKIP = {'rna_type', 'dimensions', 'matrix_world', 'matrix_basis', 'matrix_local', 'matrix_parent_inverse'}
_MAX_ITEMS = 16  # items per collection (modifiers, nodes, inputs...)
_DEPTH = 4
_BUDGET = 20000

_mode = None  # dict while Map Mode runs
RESNAP = .2  # seconds between two snapshots of the same ID (the scene takes ~20 ms)
CLICK_WINS = 2.0  # seconds a clicked value stays armed even if something else changes (e.g. Motion FX refresh)


def is_active():
    return _mode is not None


def armed_label():
    if _mode is None or not _mode.get("armed"):
        return ""
    return _mode.get("armed_label") or _mode["armed"]


def last_mapped():
    return "" if _mode is None else _mode.get("last", "")


# ---------------------------------------------------------------- change detection

def _quote(name):
    return '"' + name.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _walk(struct, prefix, depth, out):
    """Flat {data path: value} of the editable numbers / checkboxes / dropdowns of struct."""
    for prop in struct.bl_rna.properties:
        ident = prop.identifier
        if ident in _SKIP or len(out) > _BUDGET:
            continue
        path = prefix + ("." if prefix else "") + ident
        try:
            kind = prop.type
            if kind in ('FLOAT', 'INT', 'BOOLEAN'):
                if prop.is_readonly or prop.subtype == 'MATRIX':
                    continue
                value = getattr(struct, ident)
                if getattr(prop, "is_array", False):
                    for i, v in enumerate(value[:16]):
                        if isinstance(v, (int, float, bool)):
                            out["{}[{}]".format(path, i)] = v
                else:
                    out[path] = value
            elif kind == 'ENUM':
                if not prop.is_readonly and not prop.is_enum_flag:
                    out[path] = getattr(struct, ident)
            elif kind == 'POINTER' and depth > 0:
                value = getattr(struct, ident)
                if value is None or (isinstance(value, bpy.types.ID) and not value.is_embedded_data):
                    continue
                _walk(value, path, depth - 1, out)
            elif kind == 'COLLECTION' and depth > 0:
                for i, item in enumerate(getattr(struct, ident)):
                    if i >= _MAX_ITEMS or isinstance(item, bpy.types.ID):
                        break
                    name = getattr(item, "name", None)
                    key = "{}[{}]".format(path, _quote(name) if isinstance(name, str) and name else i)
                    _walk(item, key, depth - 1, out)
        except Exception:
            continue
    if isinstance(struct, bpy.types.ID) and not prefix:
        for key in struct.keys():
            value = struct[key]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out["[{}]".format(_quote(key))] = value
    return out


def snapshot(idb):
    return _walk(idb, "", _DEPTH, {})


def changed(before, after):
    """Data paths whose value changed (sorted for a stable pick)."""
    return sorted(path for path, value in after.items() if path in before and before[path] != value)


def _on_depsgraph(scene, depsgraph):
    if _mode is None:
        return
    for update in depsgraph.updates:
        idb = getattr(update.id, "original", update.id)
        if isinstance(idb, bpy.types.ID):
            _mode["pending"].add(idb.as_pointer())
            _mode["ids"][idb.as_pointer()] = idb


def _watch(idb):
    if idb is not None and _mode is not None and idb.as_pointer() not in _mode["snapshots"]:
        _mode["snapshots"][idb.as_pointer()] = snapshot(idb)


def _start_watching(context):
    obj = context.active_object
    for idb in (context.scene, context.scene.world, obj, getattr(obj, "data", None),
                getattr(obj, "active_material", None)):
        _watch(idb)
    material = getattr(obj, "active_material", None)
    if material is not None and material.node_tree is not None:
        _watch(material.node_tree)


def process_changes():
    """Arm the value the user just changed (ignoring what MIDI Mappings wrote). Returns the full path or ""."""
    if _mode is None or not _mode["pending"]:
        return ""
    pending, _mode["pending"] = _mode["pending"], set()
    ours = mapping.written.copy()
    mapping.written.clear()
    found = ""
    now = time.monotonic()
    times = _mode.setdefault("snap_times", {})
    for pointer in pending:
        if now - times.get(pointer, -RESNAP) < RESNAP:
            _mode["pending"].add(pointer)  # look again on a later tick
            continue
        times[pointer] = now
        idb = _mode["ids"].get(pointer)
        try:
            if HELPER_KEY in idb or INDEX_KEY in idb:
                continue  # AudVis moves these itself
            after = snapshot(idb)
        except ReferenceError:
            continue
        before = _mode["snapshots"].get(pointer)
        _mode["snapshots"][pointer] = after
        if before is None:
            continue  # first time we see this ID: next change counts
        for path in changed(before, after):
            plain, index = path, -1
            match = mapping._INDEX.match(path)
            if match is not None:
                plain, index = match.group(1), int(match.group(2))
            if (pointer, plain, index) in ours:
                continue
            full = mapping.full_path_of(idb, plain, index)
            try:
                mapping.parse(full)
            except ValueError:
                continue
            found = found or full
    return found


# ---------------------------------------------------------------- hover

def hovered_at(window, x, y):
    """Full data path of the button under the mouse at window coordinates x, y."""
    for area in window.screen.areas:
        if not (area.x <= x < area.x + area.width and area.y <= y < area.y + area.height):
            continue
        for region in area.regions:
            if region.x <= x < region.x + region.width and region.y <= y < region.y + region.height:
                with bpy.context.temp_override(window=window, area=area, region=region):
                    prop = getattr(bpy.context, "property", None)
                    if prop:
                        full = mapping.full_path_of(*prop)
                        try:
                            mapping.parse(full)
                            return full
                        except ValueError:
                            return ""
                return ""
    return ""


# ---------------------------------------------------------------- operator

def arm(full_path):
    if _mode is None or not full_path or ".midi_realtime." in full_path:  # not the mapping settings themselves
        return
    _mode["armed"] = full_path
    try:
        m = type("M", (), {})()
        m.id_type, m.id_name, m.data_path, m.index = mapping.parse(full_path)
        target = mapping.resolve(m)
        _mode["armed_label"] = target.label() if target is not None else full_path
    except ValueError:
        _mode["armed_label"] = full_path


def assign(scene, msg):
    """Map the knob of msg to the armed value. Re-uses an existing mapping of that value."""
    kind = 'cc' if hasattr(msg, "control") else 'note'
    number = msg.control if kind == 'cc' else msg.note
    maps = scene.audvis.midi_realtime.maps
    m = next((m for m in maps if m.target == 'property' and m.full_path == _mode["armed"]), None)
    if m is None:
        m = mapping.create(scene, kind, number, msg.channel, full_path=_mode["armed"])
    else:
        m.kind, m.number, m.channel = kind, number, msg.channel
        mapping.forget(m)
        scene.audvis.midi_realtime.maps_index = list(maps).index(m)
    _mode["last"] = "{} > {}".format(mapping.source_label(m), mapping.target_label(m))
    _mode["armed"] = _mode["armed_label"] = ""
    return _mode["last"]


def _status(context):
    if context.workspace is None or _mode is None:
        return
    if _mode.get("armed"):
        text = "AudVis Map Mode - {}: move a knob, fader or pad (Esc: exit)".format(armed_label())
    else:
        text = "AudVis Map Mode - click a value to map (Esc: exit)" + (
            "   Last: " + _mode["last"] if _mode.get("last") else "")
    context.workspace.status_text_set(text)


def _redraw(context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


class AUDVIS_OT_midiMapMode(Operator):
    """Map Mode: click any value, then move a knob, fader or pad to map it. Repeat; click again or Esc to exit"""
    bl_idname = "audvis.midi_map_mode"
    bl_label = "MIDI Map Mode"

    _timer = None

    @staticmethod
    def _analyzer(scene):
        if not scene.audvis.midi_realtime.enable:
            return None
        return bpy.audvis.get_midi_realtime_analyzer(scene)

    def invoke(self, context, event):
        global _mode
        if _mode is not None:  # the button again: switch off
            _mode["stop"] = True
            return {'FINISHED'}
        analyzer = self._analyzer(context.scene)
        if analyzer is None:
            self.report({'ERROR'}, "Enable MIDI Realtime and add your controller first")
            return {'CANCELLED'}
        _mode = {"scene": context.scene.name, "start_msg": analyzer.get_last_msg(), "armed": "",
                 "armed_label": "", "last": "", "pending": set(), "ids": {}, "snapshots": {}, "stop": False,
                 "started": time.monotonic()}
        _start_watching(context)
        mapping.written.clear()
        if _on_depsgraph not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph)
        self._timer = context.window_manager.event_timer_add(.05, window=context.window)
        context.window_manager.modal_handler_add(self)
        _status(context)
        _redraw(context)
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        global _mode
        _mode = None
        if _on_depsgraph in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph)
        context.window_manager.event_timer_remove(self._timer)
        if context.workspace is not None:
            context.workspace.status_text_set(None)
        _redraw(context)

    def modal(self, context, event):
        if _mode is None:
            return {'CANCELLED'}
        scene = bpy.data.scenes.get(_mode["scene"])
        if _mode["stop"] or scene is None or (event.type == 'ESC' and event.value == 'PRESS'):
            self._finish(context)
            return {'FINISHED'}
        if event.type in ('LEFTMOUSE', 'RIGHTMOUSE') and event.value == 'PRESS':
            full = hovered_at(context.window, event.mouse_x, event.mouse_y)
            if full:
                arm(full)
                _mode["clicked_at"] = time.monotonic()
                _status(context)
                _redraw(context)
            return {'PASS_THROUGH'}
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        analyzer = self._analyzer(scene)
        if analyzer is None:
            self.report({'WARNING'}, "MIDI Realtime stopped - Map Mode off")
            self._finish(context)
            return {'CANCELLED'}
        touched = process_changes()
        recent_click = time.monotonic() - _mode.get("clicked_at", -CLICK_WINS) < CLICK_WINS
        if touched and touched != _mode["armed"] and not recent_click:
            arm(touched)
            _status(context)
            _redraw(context)
        msg = analyzer.get_last_msg()
        if msg is not None and msg is not _mode["start_msg"] and (hasattr(msg, "control") or msg.on):
            _mode["start_msg"] = msg
            if _mode["armed"]:
                self.report({'INFO'}, assign(scene, msg))
                _mode["clicked_at"] = -CLICK_WINS
                _status(context)
                _redraw(context)
        return {'PASS_THROUGH'}


def draw_button(layout, context):
    """The Map Mode toggle and what it's doing - used by the MIDI panels."""
    col = layout.column(align=True)
    row = col.row(align=True)
    row.scale_y = 1.5
    on = is_active()
    row.operator("audvis.midi_map_mode", text="Map Mode: ON (click to stop)" if on else "Map Mode",
                 icon='REC' if on else 'EVENT_M', depress=on)
    if on:
        box = col.box().column(align=True)
        if armed_label():
            box.label(text=armed_label(), icon='RADIOBUT_ON')
            box.label(text="Now move a knob, fader or pad")
        else:
            box.label(text="Click a value to map", icon='RESTRICT_SELECT_OFF')
        if last_mapped():
            box.label(text="Mapped: " + last_mapped(), icon='CHECKMARK')


def unregister():
    global _mode
    _mode = None
    if _on_depsgraph in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph)


classes = [
    AUDVIS_OT_midiMapMode,
]
