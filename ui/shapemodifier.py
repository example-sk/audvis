import bpy
from bpy.types import (
    Panel,
    Operator,
)

from . import ui_lib
from .buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel
from .hz_label import hz_label, notes_label


def calc_freq_step(self):
    if self.freq_step_enable:
        return self.freq_step
    return self.freqrange


def order_enum(self, context):
    return [
        ("asc", "1,2,3...", "ascending"),
        ("desc", "...3,2,1", "descending"),
        ("rand", "random", "random")
    ]


def animation_type_enum(self, context):
    obj = self.id_data
    if obj is None:
        return [('0', '', '')]
    ret = [
        ("normal", "Normal", ""),
        ("location-z", "Location Z", ""),
        ("location", "Location", "Set the vector by which you want to move the vertices"),
        ("track", "Track to Object", "Select an object to track it")
    ]
    if obj.type == 'MESH':
        ret.append(("weight", "Vertex Group Weight", ""))
        ret.append(("uv", "UV map", ""))
        ret.append(("vertcolor", "Vertex Color", ""))
    # !!! skin radius unsupported in shape keys
    # if obj.type == 'MESH' and len(obj.data.skin_vertices):
    #     ret.append(("skin-radius", "Skin Radius", ""))
    if obj.type in ('CURVE', 'SURFACE'):
        ret.append(("curve-radius", "Curve Radius", ""))
        ret.append(("curve-tilt", "Curve Tilt", ""))
    if obj.type == 'GPENCIL':
        ret += [
            ("pressure", "Pressure", ""),
            ("strength", "Strength", ""),
        ]
    return ret


def gpencil_layer_changed(self, context):
    self.gpencil_layer_changed = True


class AUDVIS_PT_shapemodifier(Panel):
    bl_label = "Shape Modifier"

    @classmethod
    def poll(cls, context):
        return True

    def draw_header(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.audvis, "shapemodifier_enable", text="")

    def draw(self, context):
        obj = context.active_object or context.object
        if obj is None or obj.type not in ['MESH', 'CURVE', 'SURFACE', 'LATTICE', 'GPENCIL']:
            col = self.layout.column(align=True)
            col.label(text="Select Object")
            return
        props = obj.audvis.shapemodifier
        col = self.layout.column(align=True)
        col.prop(props, "enable", text=obj.name)
        col.prop(props, "animtype")
        col.prop(props, "operation")

        col.prop(props, "freq_seq_type")
        if props.freq_seq_type == "classic":
            col.prop(props, "freqrange")
            col.prop(props, "freqstart")
            col.prop(props, "freq_step_enable")
            if props.freq_step_enable:
                col.prop(props, "freq_step")
        elif props.freq_seq_type == "notes":
            col.prop(props, "note_a4_freq")
            col.prop(props, "note_step")
            col.prop(props, "note_offset")
        elif props.freq_seq_type == "midi":
            col.prop(props.midi, "offset")

        if props.freq_seq_type != "midi":
            self._calc_freq_range(obj, col)
        col = self.layout.column(align=True)
        if props.animtype == 'location':
            col.prop(props, "vector")
        elif props.animtype == 'uv':
            col.prop(props, "uv_vector")
        elif props.animtype == 'vertcolor':
            col.prop(props, "vertcolor_color")
        elif props.animtype == 'track':
            col.prop(props, "track_object")
        col.prop(props, "factor")
        col.prop(props, "add")
        col.prop(props, "order")
        if props.order == 'rand':
            col.prop(props, "random_seed")
        if obj.type in ('MESH',) and props.animtype in ('normal', 'location-z', 'location', 'track'):
            col.prop(props, "use_vertexgroup")
        row = col.row()
        row.label(text="additive")
        row.prop(props, "Additive", text="")
        if props.additive == 'mod':
            col.prop(props, "additive_modulus")
        if props.additive in ('sin', 'sin2', 'mod'):
            col.prop(props, "additive_phase_multiplier")
            col.prop(props, "additive_phase_offset")
        if obj.type == 'GPENCIL':
            col.prop_search(props, "gpencil_layer", obj.data, "layers",
                            icon='OUTLINER_DATA_GP_LAYER')
        if props.freq_seq_type == "midi":
            ui_lib.generators_ui_midi(self, context, props.midi)
        else:
            ui_lib.generators_ui_sequence(self, context, props)
        col = self.layout.column(align=True)
        if props.is_baking:
            col.label(text="Baking, please wait...")
            col.label(text="Press ESC to cancel baking")
        else:
            col.operator("audvis.shapemodifier_bake")
            col.operator("audvis.shapemodifier_unbake")

    def _calc_freq_range(self, obj, col):
        props = obj.audvis.shapemodifier
        count = 0
        if obj.type == 'MESH':
            count = len(obj.data.vertices)
        elif obj.type == 'LATTICE':
            count = len(obj.data.points)
        elif obj.type == 'CURVE' or obj.type == 'SURFACE':
            count = 0
            for spline in obj.data.splines:
                count += len(spline.bezier_points) + len(spline.points)
        if count:
            if props.freq_seq_type == 'notes':
                whole_range_text = notes_label(count, props.note_step, props.note_a4_freq, props.note_offset)
            else:
                whole_range_text = hz_label(start=props.freqstart,
                                            range_per_point=props.freqrange,
                                            step=calc_freq_step(props),
                                            points_count=count)
            col.label(text=whole_range_text)


# TODO: subframes
class AUDVIS_OT_shapemodifierbake(Operator):
    bl_idname = "audvis.shapemodifier_bake"
    bl_label = "Bake Shape Modifier"

    return_frame = -1
    cur_frame = -1
    end_frame = -1
    timer = None
    obj = None

    @classmethod
    def poll(self, context):
        obj = context.active_object or context.object
        if obj is None:
            return False
        if not context.scene.audvis.shapemodifier_enable:
            return False
        if not obj.audvis.shapemodifier.enable:
            return False
        return True

    def invoke(self, context, event):
        self.obj = context.active_object or context.object
        scene = context.scene
        bpy.ops.screen.animation_cancel()
        self.return_frame = scene.frame_current
        self.cur_frame = scene.frame_start
        self.end_frame = scene.frame_end
        self.obj.audvis.shapemodifier.is_baking = True  # START
        context.scene.frame_set(self.cur_frame)
        self.timer = context.window_manager.event_timer_add(.0000001, window=context.window)
        # context.window_manager.progress_begin(scene.frame_start, scene.frame_end)
        context.workspace.status_text_set("AudVis: Baking Shape Modifier")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        return {'RUNNING_MODAL'}

    def _end(self, context):
        self.obj.audvis.shapemodifier.is_baking = False  # STOP
        self.obj.audvis.shapemodifier.enable = False
        context.scene.frame_set(self.return_frame)
        context.window_manager.event_timer_remove(self.timer)
        # context.window_manager.progress_end()
        context.workspace.status_text_set(None)

    def modal(self, context, event):
        if event.type == 'TIMER':
            context.scene.frame_set(self.cur_frame)
            # context.window_manager.progress_update(self.cur_frame)
            start = context.scene.frame_start
            perc = int(((self.cur_frame - start) / (self.end_frame - start)) * 100)
            context.workspace.status_text_set("AudVis: Baking Shape Modifier: {}%".format(perc))
            if self.cur_frame >= self.end_frame:
                self._end(context)
                return {'FINISHED'}
            self.cur_frame += 1
            return {'PASS_THROUGH'}
        elif event.type == 'ESC':
            self._end(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}


class AUDVIS_OT_shapemodifierunbake(Operator):
    bl_idname = "audvis.shapemodifier_unbake"
    bl_label = "Clean Data"

    return_frame = -1
    cur_frame = -1
    end_frame = -1
    timer = None
    obj = None

    @classmethod
    def poll(self, context):
        obj = context.active_object or context.object
        if obj is None:
            return False
        if obj.type == 'GPENCIL':
            has_zero_frame = False
            for layer in obj.data.layers:
                if has_zero_frame:
                    break
                for frame in layer.frames:
                    if frame.frame_number == 0:
                        has_zero_frame = True
                        break
            if not has_zero_frame:
                return False
        return True

    def execute(self, context):
        obj = context.active_object or context.object
        if obj.type == 'GPENCIL':
            self._clean_gpencil(obj)
        else:
            for func in [self._delete_shape_key, self._delete_vertgroup, self._delete_vertexcolor, self._delete_uvmap]:
                try:
                    func(obj)
                except:
                    pass
        obj.data.update_tag()
        return {'FINISHED'}

    def _clean_gpencil(self, obj):
        for layer in obj.data.layers:
            for frame in list(layer.frames):
                if frame.frame_number > 0:
                    layer.frames.remove(frame)

    def _clean_fcurves(self, animation_data, data_path_pattern):
        try:
            fcurves = animation_data.action.fcurves
            for fcurve in list(fcurves):
                if data_path_pattern in fcurve.data_path:
                    fcurves.remove(fcurve)
        except Exception as e:
            pass

    def _delete_vertexcolor(self, obj):
        self._clean_fcurves(obj.data.animation_data, 'vertex_colors["audvis to"].')
        layer = obj.data.vertex_colors['audvis to']
        obj.data.vertex_colors.remove(layer)

    def _delete_vertgroup(self, obj):
        group = obj.vertex_groups['AudVis Target']
        self._clean_fcurves(obj.data.animation_data, ".groups[%d].weight" % group.index)
        obj.vertex_groups.remove(group)

    def _delete_shape_key(self, obj):
        try:
            self._clean_fcurves(obj.data.shape_keys.animation_data, 'key_blocks["AudVis Shape Target"].')
        except:
            pass
        key = obj.data.shape_keys.key_blocks['AudVis Shape Target']
        obj.shape_key_remove(key=key)

    def _delete_uvmap(self, obj):
        self._clean_fcurves(obj.data.animation_data, 'uv_layers["audvis to"].')
        layer = obj.data.uv_layers['audvis to']
        obj.data.uv_layers.remove(layer)


class AUDVIS_PT_shapemodifierScene(AUDVIS_PT_shapemodifier, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_shapemodifierNpanel(AUDVIS_PT_shapemodifier, SequencerButtonsPanel_Npanel):
    pass


classes = [
    AUDVIS_OT_shapemodifierbake,
    AUDVIS_OT_shapemodifierunbake,
    AUDVIS_PT_shapemodifierScene,
    AUDVIS_PT_shapemodifierNpanel,
]
