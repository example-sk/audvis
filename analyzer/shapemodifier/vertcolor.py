from . import lib


def _ensure_color(obj, name):
    if name in obj.data.vertex_colors:
        return obj.data.vertex_colors[name]
    vc = obj.data.vertex_colors.new(name=name)
    arr = [0] * (4 * len(vc.data))
    vc.data.foreach_set('color', arr)
    return vc


def modify_color(obj, scene, driver):
    settings = obj.audvis.shapemodifier
    from_name = "audvis from"
    to_name = "audvis to"
    col_from = _ensure_color(obj, from_name)
    col_to = _ensure_color(obj, to_name)
    data = [0.0] * (4 * len(col_from.data))
    col_from.data.foreach_get('color', data)
    usable_vertices_count = len(col_from.data)
    freq_indexes = lib.sorted_freq_indexes(obj.audvis.shapemodifier, usable_vertices_count)
    color = settings.vertcolor_color

    freq_i = 0
    for i in range(len(col_from.data)):
        if False:
            continue
        value = lib.calc_driver_value(settings, driver, freq_indexes[freq_i], 1)
        lib.set_value(data, i * 4 + 0, value * color[0], obj.audvis.shapemodifier.operation)
        lib.set_value(data, i * 4 + 1, value * color[1], obj.audvis.shapemodifier.operation)
        lib.set_value(data, i * 4 + 2, value * color[2], obj.audvis.shapemodifier.operation)
        freq_i += 1
    col_to.data.foreach_set('color', data)
    if obj.audvis.shapemodifier.is_baking:
        for col_vertex in col_to.data:
            col_vertex.keyframe_insert("color")
