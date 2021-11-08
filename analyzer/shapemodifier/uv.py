from . import lib


def _ensure_uv_layer(obj, name):
    if name in obj.data.uv_layers:
        return obj.data.uv_layers[name]
    return obj.data.uv_layers.new(name=name)


def modify_uv(obj, scene, driver):
    settings = obj.audvis.shapemodifier
    from_name = "audvis from"
    to_name = "audvis to"
    uv_from = _ensure_uv_layer(obj, from_name)
    uv_to = _ensure_uv_layer(obj, to_name)
    data = [0] * (2 * len(uv_from.data))
    pin_data = [False] * len(uv_from.data)
    uv_from.data.foreach_get('uv', data)
    uv_from.data.foreach_get('pin_uv', pin_data)
    usable_vertices_count = len(pin_data) - sum(pin_data)  # sum of booleans... It's stupid, but it works.
    freq_indexes = lib.sorted_freq_indexes(obj.audvis.shapemodifier, usable_vertices_count)
    uv_vector = settings.uv_vector

    freq_i = 0
    for i in range(len(uv_from.data)):
        if pin_data[i]:
            continue
        value = lib.calc_driver_value(settings, driver, freq_indexes[freq_i], 1)
        lib.set_value(data, i * 2 + 0, value * uv_vector[0], obj.audvis.shapemodifier.operation)
        lib.set_value(data, i * 2 + 1, value * uv_vector[1], obj.audvis.shapemodifier.operation)
        freq_i += 1
    uv_to.data.foreach_set('uv', data)
    if obj.audvis.shapemodifier.is_baking:
        for uv_vertex in uv_to.data:
            uv_vertex.keyframe_insert("uv")
