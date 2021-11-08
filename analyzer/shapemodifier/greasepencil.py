from random import Random

from . import lib

Random


def _get_layers(obj, all=False):
    requested_layer_name = obj.audvis.shapemodifier.gpencil_layer
    return [obj.data.layers[layer_name] for layer_name in obj.data.layers.keys()
            if all or not requested_layer_name or layer_name == requested_layer_name]


def _get_frame(layer, frame_num, move_first_available=False):
    for frame in layer.frames:
        if frame.frame_number == frame_num:
            return frame
    if move_first_available and len(layer.frames) > 0:
        frame = layer.frames[0]
        frame.frame_number = frame_num
        return frame
    return layer.frames.new(frame_num)


def _reset_strokes(layer_from, layer_to):
    while len(layer_to.strokes):
        layer_to.strokes.remove(stroke=layer_to.strokes[-1])
    for i in range(len(layer_from.strokes)):
        layer_to.strokes.new()


def _stroke(obj, stroke_from, stroke_to, driver, indexes, weights):
    settings = obj.audvis.shapemodifier
    stroke_to.line_width = stroke_from.line_width
    stroke_to.material_index = stroke_from.material_index
    points_count = len(stroke_from.points)
    if points_count != len(stroke_to.points):
        while len(stroke_to.points):
            stroke_to.points.pop(index=-1)
        stroke_to.points.add(points_count)
    locations = [0] * (3 * points_count)
    strengths = [0] * points_count
    pressures = [0] * points_count

    stroke_from.points.foreach_get('co', locations)
    stroke_from.points.foreach_get('strength', strengths)
    stroke_from.points.foreach_get('pressure', pressures)
    animtype = settings.animtype
    operation = settings.operation
    location_vector = settings.vector
    freq_step_calc = settings.freq_step_calc
    for i in range(points_count):
        index = indexes[i]
        freq_from = index * freq_step_calc + settings.freqstart
        freq_to = freq_from + settings.freqrange
        val = driver(freq_from, freq_to, ch=settings.channel) * settings.factor * weights[i] + settings.add

        if animtype == 'pressure':
            lib.set_value(pressures, i, val, operation)
        elif animtype == 'strength':
            lib.set_value(strengths, i, val, operation)
        elif animtype == 'location-z':
            lib.set_value(locations, i * 3 + 2, val, operation)
        elif animtype == 'location':
            lib.location_setter.vector(locations, i, location_vector * val, operation)
        elif animtype == 'normal':
            normal = stroke_from.points[i].co.normalized()
            lib.location_setter.vector(locations, i, normal * val, operation)
        elif animtype == 'track' and settings.track_object is not None:
            loc = stroke_from.points[i].co
            lib.location_setter.track_to(locations, i, loc, val, obj, settings, operation)

    stroke_to.points.foreach_set('co', locations)
    stroke_to.points.foreach_set('strength', strengths)
    stroke_to.points.foreach_set('pressure', pressures)
    return points_count


def _get_points_count(obj, frame_num, reset=False):
    cnt = 0
    for layer in _get_layers(obj, reset):
        frame = _get_frame(layer, frame_num)
        for stroke in frame.strokes:
            cnt += len(stroke.points)
    return cnt


def _get_weights(obj, points_count):
    # disabled because python api for grease pencil vertex groups is not working. 2019-12-31
    if False and obj.audvis.shapemodifier.use_vertexgroup:
        g = obj.vertex_groups['AudVis Location Weight']
        ret = []
        for i in range(points_count):
            try:
                val = g.weight(i)
            except:  # not in group
                val = -1
            ret.append(val)
        return ret
    else:
        return [1] * points_count


def modify_greasepencil(obj, scene, driver, reset=False):
    if not reset and obj.audvis.shapemodifier.gpencil_layer_changed:
        obj.audvis.shapemodifier.gpencil_layer_changed = False
        modify_greasepencil(obj, scene, driver, reset=True)
    frame_from = 0
    frame_to = 1
    if obj.audvis.shapemodifier.is_baking:
        frame_to = scene.frame_current
    for layer in _get_layers(obj, reset):
        _get_frame(layer, frame_from, move_first_available=True)  # just for move_first_available
    points_count = _get_points_count(obj, frame_from, reset)
    indexes = list(range(points_count))
    weights = _get_weights(obj, points_count)
    if reset:
        weights = [0] * len(weights)
    sort = obj.audvis.shapemodifier.order  # asc, desc, rand
    if sort == 'desc':
        indexes = indexes[::-1]
    elif sort == 'rand':
        Random(obj.audvis.shapemodifier.random_seed).shuffle(indexes)
    indexes_i = 0
    for layer in _get_layers(obj, reset):
        layer_from = _get_frame(layer, frame_from, move_first_available=True)
        layer_to = _get_frame(layer, frame_to)
        if len(layer_from.strokes) != len(layer_to.strokes):
            _reset_strokes(layer_from, layer_to)
        for i in range(len(layer_from.strokes)):
            indexes_i += _stroke(obj, layer_from.strokes[i], layer_to.strokes[i], driver,
                                 indexes[indexes_i:], weights[indexes_i:])
