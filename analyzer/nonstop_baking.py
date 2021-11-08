def bake(scene):
    coll = scene.audvis.nonstop_baking_collection
    if coll is not None:
        for obj in coll.all_objects:
            _obj(obj)


def _obj(obj):
    animdata = obj.animation_data
    if animdata is None:
        return
    if animdata.drivers is None:
        return
    for fcurve in animdata.drivers:
        if fcurve.driver is None:
            continue
        if fcurve.driver.type != 'SCRIPTED':
            continue
        if "audvis(" not in fcurve.driver.expression:
            continue
        path = fcurve.data_path
        index = fcurve.array_index
        _insert_keyframe(obj, path, index)

    obj.animation_data


def _insert_keyframe(obj, path, index):
    try:
        obj.keyframe_insert(path, index=index)
    except:
        obj.keyframe_insert(path)
