import bpy
from bpy.types import Panel

from .generate import Generator
from ..buttonspanel import SequencerButtonsPanel, SequencerButtonsPanel_Npanel
from ..hz_label import hz_label, notes_label


def curve_poll(self, obj):
    return obj.type == 'CURVE'


def collection_poll(self, coll):
    return "AudVisExample" not in coll.name


class AUDVIS_PT_Generator(Panel):
    bl_label = "Generate Example Objects"

    xcount: bpy.props.IntProperty(default=5)
    ycount: bpy.props.IntProperty(default=5)

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align=True)
        col.label(text="Generates some objects with")
        col.label(text=" drivers on selected properties")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Shape:")
        col.prop(scene.audvis, "example_shape", text="")
        if scene.audvis.example_shape == 'circle':
            col.prop(scene.audvis, "example_circle_radius")
        elif scene.audvis.example_shape == 'curve':
            col.prop(scene.audvis, "example_curve_object", text="Object:")
            col.prop(scene.audvis, "example_curve_axis", text="Axis:")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Basic settings:")
        col.prop(scene.audvis, "example_xcount")
        col.prop(scene.audvis, "example_ycount")
        col.prop(scene.audvis, "example_zcount")
        col.prop(scene.audvis, "example_width")
        col.prop(scene.audvis, "example_objectsize_type", text="Scale")
        if scene.audvis.example_objectsize_type == 'relative':
            col.prop(scene.audvis, "example_objectsize")
        elif scene.audvis.example_objectsize_type == 'fixed':
            col.prop(scene.audvis, "example_objectsize_fixed_value")
        col = box.column(align=True)

        col.prop(scene.audvis, "example_freq_seq_type")
        if scene.audvis.example_freq_seq_type == "classic":
            col.prop(scene.audvis, "example_rangeperobject")
            col.prop(scene.audvis, "example_freqstart")
            col.prop(scene.audvis, "example_freq_step_enable")
            if scene.audvis.example_freq_step_enable:
                col.prop(scene.audvis, "example_freq_step")
        elif scene.audvis.example_freq_seq_type == "notes":
            col.prop(scene.audvis, "example_note_a4_freq")
            col.prop(scene.audvis, "example_note_step")
            col.prop(scene.audvis, "example_note_offset")

        obj_count = (scene.audvis.example_xcount * scene.audvis.example_ycount * scene.audvis.example_zcount)
        step = scene.audvis.example_freq_step
        if not scene.audvis.example_freq_step_enable:
            step = scene.audvis.example_rangeperobject
        if scene.audvis.example_freq_seq_type == 'notes':
            whole_range_text = notes_label(obj_count, scene.audvis.example_note_step, scene.audvis.example_note_a4_freq,
                                           scene.audvis.example_note_offset)
        else:
            whole_range_text = hz_label(start=scene.audvis.example_freqstart,
                                        range_per_point=scene.audvis.example_rangeperobject,
                                        step=step,
                                        points_count=obj_count)
        col.label(text=whole_range_text)

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Objects:")
        col.prop(scene.audvis, "example_object_type", text="Objects Type")
        if scene.audvis.example_object_type == 'Select Object:':
            row = col.row()
            row.label(text="Object")
            row.prop_search(scene.audvis, "example_object", bpy.data, "objects", text="")
        elif scene.audvis.example_object_type == 'Random From Collection:':
            row = col.row()
            row.label(text="Collection")
            row.prop_search(scene.audvis, "example_collection", bpy.data, "collections", text="")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Driver:")
        col.prop(scene.audvis, "example_driver_add")
        col.prop(scene.audvis, "example_driver_factor")

        if scene.audvis.example_object_type == 'Select Object:':
            col.prop(scene.audvis, "example_driver_objectdrivers")
        row = col.row()
        row.label(text="Scale Animation")
        row.prop(scene.audvis, "example_driver_scalex", text="X")
        row.prop(scene.audvis, "example_driver_scaley", text="Y")
        row.prop(scene.audvis, "example_driver_scalez", text="Z")
        row = col.row()
        row.label(text="Location Animation")
        row.prop(scene.audvis, "example_driver_locx", text="X")
        row.prop(scene.audvis, "example_driver_locy", text="Y")
        row.prop(scene.audvis, "example_driver_locz", text="Z")
        row = col.row()
        row.label(text="Rotation Animation")
        row.prop(scene.audvis, "example_driver_rotx", text="X")
        row.prop(scene.audvis, "example_driver_roty", text="Y")
        row.prop(scene.audvis, "example_driver_rotz", text="Z")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Sound:")
        if scene.sequence_editor is not None:
            col.prop_search(scene.audvis, "example_sound_sequence", scene.sequence_editor, "sequences",
                            icon='SOUND')
        col.prop(scene.audvis, "example_channel")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Additional settings:")
        col.prop(scene.audvis, "example_randomize_location")
        col.prop(scene.audvis, "example_randomize_rotation")
        col.prop(scene.audvis, "example_randomize_scale")
        col.prop(scene.audvis, "example_lattice")
        col.prop(scene.audvis, "example_empty")

        col.label(text="Material:")
        col.prop(scene.audvis, "example_material", text="")
        if scene.audvis.example_material == 'None':
            pass
        elif scene.audvis.example_material == 'Copy+Modify':
            col.prop(scene.audvis, "example_material_material")
        else:
            col.prop(scene.audvis, "example_material_basecolor")
            col.prop(scene.audvis, "example_material_channel")

        col.label(text="Collections:")
        col.prop(scene.audvis, "example_collections_action", text="")

        col = layout.column(align=True)
        col.operator("audvis.generate")


class AUDVIS_PT_GeneratorScene(AUDVIS_PT_Generator, SequencerButtonsPanel):
    bl_parent_id = "AUDVIS_PT_audvisScene"


class AUDVIS_PT_GeneratorNpanel(AUDVIS_PT_Generator, SequencerButtonsPanel_Npanel):
    pass


class AUDVIS_OT_Generate(bpy.types.Operator):
    bl_idname = "audvis.generate"
    bl_label = "Generate AudVis Example"

    def execute(self, context):
        Generator(context).generate()
        return {'FINISHED'}


classes = [
    AUDVIS_OT_Generate,
    AUDVIS_PT_GeneratorScene,
    AUDVIS_PT_GeneratorNpanel,
]
