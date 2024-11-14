import bpy
import pathlib

from ..arrangement import Arrangement
from ...props.daw_arrangement import AudvisDawArrangement


class GeometryNodes1:
    props: AudvisDawArrangement
    arrangement: Arrangement

    def make(self, context, dawarrangement: Arrangement):
        scene = context.scene
        self.scene = scene
        self.arrangement = dawarrangement
        self.props = scene.audvis.daw_arrangement
        props = self.props
        if props.last_collection is not None and props.replace_last_collection:
            for clips_obj in props.last_collection.objects:
                props.last_collection.objects.unlink(clips_obj)
                bpy.data.objects.remove(clips_obj)
            bpy.data.collections.remove(props.last_collection)

        collection = bpy.data.collections.new('dawarrangement')
        props.last_collection = collection
        self.master_parent = bpy.data.objects.new('dawarrangement superparent', None)
        collection.objects.link(self.master_parent)
        txt_curve = bpy.data.curves.new(type="FONT", name='track names')
        txt_parent = bpy.data.objects.new('track labels parent', None)
        txt_parent.parent = self.master_parent
        collection.objects.link(txt_parent)
        scene.collection.children.link(collection)
        mesh = self.init_mesh(dawarrangement)
        notes_mesh = self.init_mesh(dawarrangement)
        y = 0.0
        default_height = props.line_height
        y_margin = props.line_margin
        for track in dawarrangement.tracks:
            if len(track.clips) == 0:
                continue
            txt_curve.body = txt_curve.body + track.name + "\n"
            self.render_track_name(track, collection, txt_parent, y)
            for clip in track.clips:
                mesh.vertices.add(1)
                mesh.update()
                vertex = mesh.vertices[-1]
                vertex.co = [
                    clip.time * self.props.zoom,
                    -y,
                    0
                ]
                mesh.attributes['width'].data[-1].value = clip.duration * self.props.zoom
                mesh.attributes['height'].data[-1].value = props.line_height
                mesh.attributes['clr'].data[-1].color = clip.color
                self.add_notes(clip, notes_mesh, y)
                # clip.parse_soundwave(bpy_arrangement.helper_action, "/home/r/Music/kodiki/4009433672.mp3",
                #                     [(0, 0), (168.6564235687256, 11.89120014912915),
                #                      (299.2837886810303, 112.24828873200025), (341.9036741256714, 128.156735)])
            y = y + default_height + y_margin

        clips_obj = bpy.data.objects.new('daw arrangement clips', mesh)
        clips_obj.parent = self.master_parent
        notes_obj = bpy.data.objects.new('daw arrangement notes', notes_mesh)
        notes_obj.parent = self.master_parent
        if props.track_name_position == "0":
            pass
        elif props.track_name_position == "1":
            txt_parent.location[2] = props.thickness_clip
        elif props.track_name_position == "2":
            txt_parent.location[2] = props.thickness_clip + props.thickness_note

        collection.objects.link(clips_obj)
        collection.objects.link(notes_obj)
        self.add_geonodes_and_animate(clips_obj, self.props.thickness_clip)
        self.add_geonodes_and_animate(notes_obj, self.props.thickness_note)
        self.select(context, clips_obj)

    def add_geonodes_and_animate(self, obj, thickness: float):
        props = self.props
        scene = self.scene
        arrangement = self.arrangement
        geonodes_modifier = obj.modifiers.new(name="DawArrangement", type="NODES")
        geonodes_modifier.node_group = bpy.data.node_groups['DawArrangement']
        geonodes_modifier['Input_2'] = thickness
        obj.animation_data_create()
        if obj.animation_data.action is None:
            obj.animation_data.action = bpy.data.actions.new('NewAction')
        fcurve = obj.animation_data.action.fcurves.new(data_path='location', index=0)
        # geonodes_modifier['Input_5'] = 0
        time_points = arrangement.calc_tempo_to_time()
        for time_point in time_points:
            frame = (time_point[0] * scene.render.fps * scene.render.fps_base) + props.frame_start
            obj.location[0] = -time_point[1] * props.zoom
            obj.keyframe_insert(data_path=self.master_parent.path_from_id('location'), index=0, frame=frame)
        for keyframe_point in fcurve.keyframe_points:
            keyframe_point.interpolation = 'LINEAR'

    def select(self, context, obj):
        context.view_layer.update()
        for o in context.view_layer.objects.selected:  # unselect all objects
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        context.view_layer.update()

    def render_track_name(self, track, collection, txt_parent, y):
        curve = bpy.data.curves.new(type="FONT", name='track name ' + track.name)
        curve.size = bpy.context.scene.audvis.daw_arrangement.line_height
        obj = bpy.data.objects.new('track name ' + track.name, curve)
        curve.align_y = 'TOP'
        curve.align_x = 'RIGHT'
        obj.data.body = track.name
        collection.objects.link(obj)
        obj.location[1] = -y
        obj.parent = txt_parent
        curve.materials.append(bpy.data.materials['daw track name'])
        curve.bevel_depth = self.props.track_name_bevel_depth
        if track.color is not None:
            obj.color = track.color

    def add_notes(self, clip, mesh, y):
        if len(clip.notes) == 0:
            return
        notes_range = clip.get_notes_range()
        notes_range_size = notes_range[1] - notes_range[0] + 1
        if notes_range_size < 1:
            notes_range_size = 1
        mesh.vertices.add(len(clip.notes))
        index = -1
        padding = self.props.line_height * (self.props.clip_padding / 100)
        notes_line_height = self.props.line_height - padding
        for note in clip.notes:
            vertex = mesh.vertices[index]
            vertex.co = [
                (note.time + clip.time) * self.props.zoom,
                -y - (padding / 2) - ((note.key - notes_range[0]) / notes_range_size) * notes_line_height,
                self.props.thickness_clip
            ]
            mesh.attributes['width'].data[index].value = note.duration * self.props.zoom
            mesh.attributes['height'].data[index].value = notes_line_height / notes_range_size
            mesh.attributes['clr'].data[index].color = clip.color
            index -= 1

    def init_mesh(self, dawarrangement: Arrangement):
        mesh = bpy.data.meshes.new(dawarrangement.name if dawarrangement.name is not None else 'dawarrangement')
        mesh.attributes.new('width', 'FLOAT', 'POINT')
        mesh.attributes.new('height', 'FLOAT', 'POINT')
        mesh.attributes.new('clr', 'FLOAT_COLOR', 'POINT')
        return mesh
