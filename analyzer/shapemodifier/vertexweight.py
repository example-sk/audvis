from random import Random

from . import lib


def ensure_vertex_group(obj, name):
    if name in obj.vertex_groups:
        return obj.vertex_groups[name]
    grp = obj.vertex_groups.new(name=name)
    grp.add(list(range(len(obj.data.vertices))), 0, 'REPLACE')
    return grp


def modify_vertex_weight(obj, scene, driver):
    if obj.type != 'MESH' or obj.mode == 'EDIT':
        return
    grp_orig = ensure_vertex_group(obj, 'AudVis Origin')
    grp_target = ensure_vertex_group(obj, 'AudVis Target')
    lst = []
    not_used_lst = []
    for i in range(len(obj.data.vertices)):
        used = False
        for vertgroup in obj.data.vertices[i].groups:
            if vertgroup.group == grp_orig.index:
                lst.append(i)
                used = True
        if not used:
            not_used_lst.append(i)
    grp_target.remove(not_used_lst)
    order = obj.audvis.shapemodifier.order
    operation = obj.audvis.shapemodifier.operation
    if order == 'asc':
        pass
    elif order == 'desc':
        lst = lst[::-1]
    elif order == 'rand':
        seed = obj.audvis.shapemodifier.random_seed
        Random(seed).shuffle(lst)
    for i in range(len(lst)):
        val = lib.calc_driver_value(obj.audvis.shapemodifier, driver, i, 1)
        if operation == 'add':
            try:
                orig = grp_orig.weight(lst[i])
                val += orig
            except Exception as e:
                val = 0
        grp_target.add([lst[i]], val, 'REPLACE')

    if obj.audvis.shapemodifier.is_baking:
        vertgroup_index = grp_target.index
        for vertex in obj.data.vertices:
            for group in vertex.groups:
                if group.group == vertgroup_index:
                    group.keyframe_insert("weight")
                    break
