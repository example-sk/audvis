from . import lib
from . import vertexweight, greasepencil, uv, vertcolor
from ..analyzer import Analyzer


def ensure_vertex_group(obj):
    name = "AudVis Location Weight"
    if name in obj.vertex_groups:
        return obj.vertex_groups[name]
    grp = obj.vertex_groups.new(name=name)
    grp.add(list(range(len(obj.data.vertices))), 1, 'REPLACE')
    return grp


def create_shapemodifier_vertgroup(props, context):
    obj = props.id_data
    if props.use_vertexgroup:
        ensure_vertex_group(obj)


def _get_vertgroup_weight(obj, vertex_index, group_index):
    for grp in obj.data.vertices[vertex_index].groups:
        if grp.group == group_index:
            return grp.weight
    return -1


class ShapeModifier(Analyzer):
    _driver = None

    def load(self, driver):
        self._driver = driver

    def stop(self):
        pass

    def on_pre_frame(self, scene, frame):
        objects = []
        if scene.sequence_editor is not None:
            for seq in scene.sequence_editor.sequences_all:
                if seq.frame_final_start <= frame <= seq.frame_final_end:
                    if seq.type == 'SCENE' and seq.scene.audvis.shapemodifier_enable:
                        objects += [obj for obj in seq.scene.objects if obj.audvis.shapemodifier.enable]
        if scene.audvis.shapemodifier_enable:
            objects += [obj for obj in scene.objects if obj.audvis.shapemodifier.enable]
        for obj in objects:
            self.modify(obj, scene)

    def _ensure_vertex_group(self, obj, name):
        if name in obj.vertex_groups:
            return obj.vertex_groups[name]
        grp = obj.vertex_groups.new(name=name)
        for i in range(len(obj.data.vertices)):
            grp.add([i], 0, 'REPLACE')
        return grp

    def modify(self, obj, scene):
        name_origin = "AudVis Shape Origin"
        name_target = "AudVis Shape Target"
        settings = obj.audvis.shapemodifier
        animtype = settings.animtype
        if animtype == 'weight':
            vertexweight.modify_vertex_weight(obj, scene, self._driver)
        elif animtype == 'uv':
            uv.modify_uv(obj, scene, self._driver)
        elif animtype == 'vertcolor':
            vertcolor.modify_color(obj, scene, self._driver)
        if obj.type == 'GPENCIL':
            greasepencil.modify_greasepencil(obj, scene, self._driver)
            return
        keys = obj.data.shape_keys
        if keys is None:
            obj.shape_key_add(name=name_origin)
            keys = obj.data.shape_keys
        if name_origin not in keys.key_blocks:
            obj.shape_key_add(name=name_origin)
        if name_target not in keys.key_blocks:
            sk = obj.shape_key_add(name=name_target)
            sk.value = 1
            sk.relative_key = obj.data.shape_keys.key_blocks[name_origin]
        shape_key_orig_data = obj.data.shape_keys.key_blocks[name_origin].data
        shape_key_target_data = obj.data.shape_keys.key_blocks[name_target].data
        #############
        vertices_count = len(shape_key_orig_data)
        if obj.type == 'MESH' and settings.use_vertexgroup:
            grp_orig_index = ensure_vertex_group(obj).index
            weights = [_get_vertgroup_weight(obj, i, grp_orig_index) for i in range(vertices_count)]
        else:
            weights = [1] * vertices_count
        #############
        usable_vertices_count = sum([1 for w in weights if w > 0])
        freq_indexes = lib.sorted_freq_indexes(settings, usable_vertices_count)
        locations = [0.0] * (vertices_count * 3)
        shape_key_orig_data.foreach_get('co', locations)
        if obj.type in ('CURVE', 'SURFACE'):
            radiuses = [0.0] * vertices_count
            shape_key_orig_data.foreach_get('radius', radiuses)
            tilts = [0.0] * vertices_count
            shape_key_orig_data.foreach_get('tilt', tilts)

        freq_i = 0
        operation = settings.operation
        for i in range(len(shape_key_orig_data)):
            weight = weights[i]
            if weight <= 0:
                continue
            val = lib.calc_driver_value(settings, self._driver, freq_indexes[freq_i], weight)
            if animtype == 'location-z':
                lib.set_value(locations, i * 3 + 2, val, operation)
            elif animtype == 'location':
                lib.location_setter.vector(locations, i, settings.vector * val, operation)
            elif animtype == 'normal':
                normal = shape_key_orig_data[i].co.normalized()
                lib.location_setter.vector(locations, i, normal * val, operation)
            elif animtype == 'vert-normal':
                normal = obj.data.vertices[i].normal
                lib.location_setter.vector(locations, i, normal * val, operation)
            elif animtype == 'track' and settings.track_object is not None:
                lib.location_setter.track_to(locations, i, shape_key_orig_data[i].co, val, obj, settings, operation)
            elif animtype == 'curve-radius':
                lib.set_value(radiuses, i, val, operation)
            elif animtype == 'curve-tilt':
                lib.set_value(tilts, i, val, operation)
            freq_i += 1
        shape_key_target_data.foreach_set('co', locations)
        if obj.type in ('CURVE', 'SURFACE'):
            shape_key_target_data.foreach_set('radius', radiuses)
            shape_key_target_data.foreach_set('tilt', tilts)
        obj.data.update_tag()
        # shape_key_target_data.update()
        if settings.is_baking and animtype not in ('uv', 'vertcolor') and obj.type != 'GPENCIL':
            for point in shape_key_target_data:
                if animtype == 'curve-radius':
                    point.keyframe_insert("radius")
                elif animtype == 'curve-tilt':
                    point.keyframe_insert("tilt")
                elif animtype == 'weight':
                    pass
                elif animtype == 'location-z':
                    point.keyframe_insert("co", index=2)
                else:
                    point.keyframe_insert("co")
