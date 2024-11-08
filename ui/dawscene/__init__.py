import pathlib

import bpy
import bpy_extras

from .parser import dawproject
from .scene import Scene
from ..buttonspanel import AudVisButtonsPanel_Npanel


class AUDVIS_OT_DawSceneTo3D(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "audvis.dawsceneto3d"
    bl_label = "Import DAW Scene"

    filepath: bpy.props.StringProperty(name=".dawscene file path", subtype='FILE_PATH', options={'SKIP_SAVE'})
    # filter_search: bpy.props.StringProperty(default="*.dawscene", options={'SKIP_SAVE'})
    filter_glob: bpy.props.StringProperty(
        default="*.dawproject",
        options={'HIDDEN'},
    )

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        self.filter_search = '*.dawproject'
        return {'RUNNING_MODAL'}

    def _render(self, context, dawscene: Scene):
        scene = context.scene
        if 'dawscene' not in bpy.data.node_groups:
            libpath = pathlib.Path(__file__).parent.resolve().__str__() + "/dawscene-blender3_6.blend"
            with bpy.data.libraries.load(libpath) as (data_from, data_to):
                data_to.materials = data_from.materials
                data_to.node_groups = data_from.node_groups
            bpy.data.libraries.remove(bpy.data.libraries[-1])
        mesh = self._init_mesh(dawscene)
        y = 0.0
        default_height = .2
        for track in dawscene.tracks:
            y = y + default_height
            for clip in track.clips:
                mesh.vertices.add(1)
                mesh.update()
                vertex = mesh.vertices[-1]
                vertex.co[0] = clip.time
                vertex.co[1] = -y
                mesh.attributes['width'].data[-1].value = clip.duration
                mesh.attributes['height'].data[-1].value = default_height
                mesh.attributes['layer'].data[-1].value = 0
                mesh.attributes['clr'].data[-1].color = clip.color
                self._add_notes(clip, mesh, default_height, y)

        obj = bpy.data.objects.new('dawscene', mesh)

        scene.collection.objects.link(obj)
        geonodes_modifier = obj.modifiers.new(name="dawscene", type="NODES")
        geonodes_modifier.node_group = bpy.data.node_groups['dawscene']
        keyframe_path = geonodes_modifier.path_from_id('["Input_5"]')
        obj.animation_data_create()
        if obj.animation_data.action is None:
            obj.animation_data.action = bpy.data.actions.new('NewAction')
        fcurve = obj.animation_data.action.fcurves.new(data_path=keyframe_path)
        geonodes_modifier['Input_5'] = 0
        time_points = dawscene.calc_tempo_to_time()
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
            print('p1 p2', [p1.co, p2.co])
        bevel_modifier = obj.modifiers.new(name="Bevel", type="BEVEL")
        bevel_modifier.width = .025
        bevel_modifier.segments = 3
        obj.modifiers.active = geonodes_modifier
        context.view_layer.update()
        for o in context.view_layer.objects.selected:  # unselect all objects
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        context.view_layer.update()
        print(context.view_layer.objects.active.name, obj.name)

    def _add_notes(self, clip, mesh, default_height, y):
        if len(clip.notes) == 0:
            return
        mesh.vertices.add(len(clip.notes))
        index = -1
        for note in clip.notes:
            vertex = mesh.vertices[index]
            vertex.co[0] = note.time + clip.time
            vertex.co[1] = -y + (note.key / 128) * default_height
            mesh.attributes['width'].data[index].value = note.duration
            mesh.attributes['height'].data[index].value = default_height / 128
            mesh.attributes['layer'].data[index].value = 1
            mesh.attributes['clr'].data[index].color = clip.color
            index -= 1

    def execute(self, context):
        if not self.filepath:
            return {'CANCELLED'}
        parsed_scene = None
        if self.filepath.endswith(".dawproject"):
            parsed_scene = dawproject.parse(self.filepath)
        # TODO: add other DAWs
        else:
            return {'CANCELLED'}
        self._render(context, parsed_scene)
        return {'FINISHED'}

    def _init_mesh(self, dawscene: Scene):
        mesh = bpy.data.meshes.new(dawscene.name if dawscene.name is not None else 'dawscene')
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
    bl_label = "Import DAW arrangement"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        col = layout.column(align=True)
        col.operator('audvis.dawsceneto3d')


classes = [
    AUDVIS_OT_DawSceneTo3D,
    AUDVIS_PT_DawprojectTo3d,
]
