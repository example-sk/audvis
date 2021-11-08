import bpy


def generate_material(audvis_config, freq_from, freq_to):
    if audvis_config.example_material == 'None':
        return None

    if audvis_config.example_material == 'Copy+Modify':
        if audvis_config.example_material_material is not None:
            return _copy_modify(audvis_config, freq_from, freq_to)
        return

    mat = bpy.data.materials.new("AudVisExample")
    if hasattr(bpy.data, "collections"):  # blender 2.80
        mat.diffuse_color = audvis_config.example_material_basecolor
    else:
        col = audvis_config.example_material_basecolor
        mat.diffuse_color = (col[0], col[1], col[2])
    if audvis_config.example_material_channel == 'gray':
        channels = [0, 1, 2]
    else:
        channels = [int(audvis_config.example_material_channel)]
    expr = "audvis(%s,%s) / 10" % (freq_from, freq_to)
    _driver_channel(mat, channels, expr)
    return mat


def _copy_modify(audvis_config, freq_from, freq_to):
    material = audvis_config.example_material_material.copy()
    if material.node_tree is not None and material.node_tree.animation_data is not None:
        for driver in material.node_tree.animation_data.drivers:
            exp = driver.driver.expression
            driver.driver.expression = exp.replace("audvis()", "audvis(%s,%s)" % (freq_from, freq_to))
    return material


def _driver_channel(mat, channels, expr):
    for ch in channels:
        d = mat.driver_add("diffuse_color", int(ch))
        d.driver.expression = expr
