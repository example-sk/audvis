import pathlib

import bpy
import bpy_extras

from .parser import (dawproject, als)
from .arrangement import Arrangement
from ..buttonspanel import AudVisButtonsPanel_Npanel


class AUDVIS_OT_DawArrangementTo3D(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "audvis.dawarrangementto3d"
    bl_label = "Import DAW Arrangement"

    filepath: bpy.props.StringProperty(name=".dawarrangement file path", subtype='FILE_PATH', options={'SKIP_SAVE'})
    # filter_search: bpy.props.StringProperty(default="*.dawarrangement", options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(
        default="*.dawproject;*.als",
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        self.filter_search = '*.dawproject;*.als'
        return {'RUNNING_MODAL'}

    def _render_track_name(self, track, collection, txt_parent, y):
        font_curve = bpy.data.curves.new(type="FONT", name='track name ' + track.name)
        font_curve.size = .5
        txt_object = bpy.data.objects.new('track name ' + track.name, font_curve)
        font_curve.align_y = 'TOP'
        font_curve.align_x = 'RIGHT'
        txt_object.data.body = track.name
        collection.objects.link(txt_object)
        txt_object.location[1] = -y
        txt_object.parent = txt_parent
        if track.color is not None:
            txt_object.color = track.color

    def _render(self, context, dawarrangement: Arrangement):
        scene = context.scene
        collection = bpy.data.collections.new('dawarrangement')
        master_parent = bpy.data.objects.new('dawarrangement superparent', None)
        txt_curve = bpy.data.curves.new(type="FONT", name='track names')
        txt_curve.size = .5
        txt_curve.space_line = 1.2
        txt_curve.align_y = 'TOP'
        txt_curve.align_x = 'RIGHT'
        txt_obj = bpy.data.objects.new('track labels parent', txt_curve)
        # txt_obj.parent = master_parent
        # collection.objects.link(txt_obj)
        scene.collection.children.link(collection)
        if 'DawArrangement' not in bpy.data.node_groups:
            libpath = pathlib.Path(__file__).parent.resolve().__str__() + "/DawArrangement-blender3_6.blend"
            with bpy.data.libraries.load(libpath) as (data_from, data_to):
                data_to.materials = data_from.materials
                data_to.node_groups = data_from.node_groups
            bpy.data.libraries.remove(bpy.data.libraries[-1])
        mesh = self._init_mesh(dawarrangement)
        y = 0.0
        default_height = .5
        y_margin = .1
        for track in dawarrangement.tracks:
            if len(track.clips) == 0:
                continue
            txt_curve.body = txt_curve.body + track.name + "\n"
            self._render_track_name(track, collection, txt_obj, y)
            for clip in track.clips:
                mesh.vertices.add(1)
                mesh.update()
                vertex = mesh.vertices[-1]
                vertex.co[0] = clip.time
                vertex.co[1] = -y
                mesh.attributes['width'].data[-1].value = clip.duration
                mesh.attributes['height'].data[-1].value = default_height
                mesh.attributes['layer'].data[-1].value = -1
                mesh.attributes['clr'].data[-1].color = clip.color
                self._add_notes(clip, mesh, default_height, y)
            y = y + default_height + y_margin

        obj = bpy.data.objects.new('dawarrangement', mesh)
        obj.parent = master_parent
        txt_obj.location[2] = .01

        collection.objects.link(obj)
        geonodes_modifier = obj.modifiers.new(name="DawArrangement", type="NODES")
        geonodes_modifier.node_group = bpy.data.node_groups['DawArrangement']
        keyframe_path = geonodes_modifier.path_from_id('["Input_5"]')
        obj.animation_data_create()
        if obj.animation_data.action is None:
            obj.animation_data.action = bpy.data.actions.new('NewAction')
        fcurve = obj.animation_data.action.fcurves.new(data_path=keyframe_path)
        geonodes_modifier['Input_5'] = 0
        time_points = dawarrangement.calc_tempo_to_time()
        fcurve.keyframe_points.add(len(time_points))
        for time_point in time_points:
            geonodes_modifier['Input_5'] = time_point[1]
            obj.keyframe_insert(data_path=keyframe_path,
                                frame=(time_point[0] * scene.render.fps * scene.render.fps_base) + scene.frame_start)
        for keyframe_point in obj.animation_data.action.fcurves[0].keyframe_points:
            keyframe_point.interpolation = 'BEZIER'
            keyframe_point.handle_left_type = 'FREE'
            keyframe_point.handle_left = keyframe_point.co
            keyframe_point.handle_right_type = 'FREE'
            keyframe_point.handle_right = keyframe_point.co
        for i in range(1, len(obj.animation_data.action.fcurves[0].keyframe_points)):
            p1 = obj.animation_data.action.fcurves[0].keyframe_points[i - 1]
            p2 = obj.animation_data.action.fcurves[0].keyframe_points[i]
            p1.handle_right = ((p1.co[0] + p2.co[0]) / 2, (p1.co[1] + p2.co[1]) / 2)
            p2.handle_left = ((p1.co[0] + p2.co[0]) / 2, (p1.co[1] + p2.co[1]) / 2)
            # print('p1 p2', [p1.co, p2.co])
        # bevel_modifier = obj.modifiers.new(name="Bevel", type="BEVEL")
        # bevel_modifier.width = .025
        # bevel_modifier.segments = 1
        obj.modifiers.active = geonodes_modifier
        context.view_layer.update()
        for o in context.view_layer.objects.selected:  # unselect all objects
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        context.view_layer.update()

    def _add_notes(self, clip, mesh, default_height, y):
        if len(clip.notes) == 0:
            return
        notes_range = clip.get_notes_range()
        notes_range_size = notes_range[1] - notes_range[0] + 1
        mesh.vertices.add(len(clip.notes))
        index = -1
        for note in clip.notes:
            vertex = mesh.vertices[index]
            vertex.co[0] = note.time + clip.time
            vertex.co[1] = -y - ((note.key - notes_range[0]) / notes_range_size) * default_height
            mesh.attributes['width'].data[index].value = note.duration
            mesh.attributes['height'].data[index].value = default_height / notes_range_size
            mesh.attributes['layer'].data[index].value = 0
            mesh.attributes['clr'].data[index].color = clip.color
            index -= 1

    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
        parsed_arrangement = None
        if self.filepath.endswith(".dawproject"):
            parsed_arrangement = dawproject.parse(self.filepath)
        elif self.filepath.endswith(".als"):
            parsed_arrangement = als.parse(self.filepath)
        # TODO: add other DAWs
        else:
            return {'CANCELLED'}
        self._render(context, parsed_arrangement)
        return {'FINISHED'}

    def _init_mesh(self, dawarrangement: Arrangement):
        mesh = bpy.data.meshes.new(dawarrangement.name if dawarrangement.name is not None else 'dawarrangement')
        mesh.attributes.new('width', 'FLOAT', 'POINT')
        mesh.attributes.new('height', 'FLOAT', 'POINT')
        mesh.attributes.new('layer', 'INT', 'POINT')
        mesh.attributes.new('clr', 'FLOAT_COLOR', 'POINT')
        return mesh


def _parse_color(input: str):
    tmp = input.lstrip('#')
    return (
        int(tmp[0:2], 16) / 255,
        int(tmp[2:4], 16) / 255,
        int(tmp[4:6], 16) / 255,
        1,
    )


class AUDVIS_PT_DawprojectTo3d(AudVisButtonsPanel_Npanel):
    bl_label = "Import DAW Arrangement"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align=True)
        col.operator('audvis.dawarrangementto3d')


classes = [
    AUDVIS_OT_DawArrangementTo3D,
    AUDVIS_PT_DawprojectTo3d,
]
