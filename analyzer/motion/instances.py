"""Instanced output for Cascade and Orbit: instead of thousands of objects, the
engine writes one point per element into a "carrier" mesh (position + rotation +
scale + color attributes) and a Geometry Nodes modifier instances the source
object on those points. Handles 10k+ elements while playing."""
import bpy
import numpy as np

GROUP = "AudVis Motion Instances"
GROUP_VERSION = 1
MODIFIER = "AudVis Instances"
AXIS, ANGLE, SCALE, COLOR = "audvis_axis", "audvis_angle", "audvis_scale", "audvis_color"


def ensure_group():
    ng = bpy.data.node_groups.get(GROUP)
    if ng is not None and ng.get("audvis_version") == GROUP_VERSION:
        return ng
    if ng is None:
        ng = bpy.data.node_groups.new(GROUP, 'GeometryNodeTree')
    ng.nodes.clear()
    ng.interface.clear()
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Instance", in_out='INPUT', socket_type='NodeSocketObject')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = ng.nodes, ng.links
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')
    info = nodes.new('GeometryNodeObjectInfo')
    info.transform_space = 'ORIGINAL'
    info.inputs["As Instance"].default_value = True
    attrs = {}
    for name, data_type in ((AXIS, 'FLOAT_VECTOR'), (ANGLE, 'FLOAT'), (SCALE, 'FLOAT_VECTOR')):
        node = nodes.new('GeometryNodeInputNamedAttribute')
        node.data_type = data_type
        node.inputs["Name"].default_value = name
        attrs[name] = node
    rotation = nodes.new('FunctionNodeAxisAngleToRotation')
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    links.new(group_in.outputs[1], info.inputs["Object"])
    links.new(group_in.outputs[0], instance.inputs["Points"])
    links.new(info.outputs["Geometry"], instance.inputs["Instance"])
    links.new(attrs[AXIS].outputs["Attribute"], rotation.inputs["Axis"])
    links.new(attrs[ANGLE].outputs["Attribute"], rotation.inputs["Angle"])
    links.new(rotation.outputs["Rotation"], instance.inputs["Rotation"])
    links.new(attrs[SCALE].outputs["Attribute"], instance.inputs["Scale"])
    links.new(instance.outputs["Instances"], group_out.inputs[0])
    for i, node in enumerate([group_in, info, *attrs.values(), rotation, instance, group_out]):
        node.location = (i * 200, 0)
    ng["audvis_version"] = GROUP_VERSION
    return ng


def create_carrier(name, source, collection):
    """Point-cloud object with the instancing modifier, instancing `source`."""
    mesh = bpy.data.meshes.new(name)
    carrier = bpy.data.objects.new(name, mesh)
    collection.objects.link(carrier)
    mod = carrier.modifiers.new(MODIFIER, 'NODES')
    mod.node_group = ensure_group()
    set_source(carrier, source)
    return carrier


def set_source(carrier, source):
    mod = carrier.modifiers.get(MODIFIER)
    if mod is None:
        return
    ident = mod.node_group.interface.items_tree["Instance"].identifier
    if hasattr(mod, "properties"):  # Blender 5.x: inputs are RNA structs with a value
        getattr(mod.properties.inputs, ident).value = source
    else:
        mod[ident] = source


def _resize(mesh, n):
    if len(mesh.vertices) == n:
        return
    mesh.clear_geometry()
    mesh.vertices.add(n)
    for name, data_type in ((AXIS, 'FLOAT_VECTOR'), (ANGLE, 'FLOAT'), (SCALE, 'FLOAT_VECTOR'), (COLOR, 'FLOAT_COLOR')):
        if name in mesh.attributes:
            mesh.attributes.remove(mesh.attributes[name])
        mesh.attributes.new(name, data_type, 'POINT')


def write(carrier, matrix_world, positions, axes, angles, scales, colors=None):
    """positions / axes / scales (n, 3), angles (n,), colors (n, 4) - all in the carrier's space."""
    carrier.matrix_world = matrix_world
    mesh = carrier.data
    n = len(positions)
    _resize(mesh, n)
    f32 = lambda a: np.ascontiguousarray(a, dtype=np.float32).ravel()
    mesh.vertices.foreach_set("co", f32(positions))
    mesh.attributes[AXIS].data.foreach_set("vector", f32(axes))
    mesh.attributes[ANGLE].data.foreach_set("value", f32(angles))
    mesh.attributes[SCALE].data.foreach_set("vector", f32(scales))
    if colors is not None:
        mesh.attributes[COLOR].data.foreach_set("color", f32(colors))
    mesh.update()


def matrices_to_arrays(matrices, base_inverse):
    """Decompose world matrices into carrier-space position, axis-angle and scale."""
    n = len(matrices)
    pos, axes, angles, scales = np.zeros((n, 3)), np.zeros((n, 3)), np.zeros(n), np.ones((n, 3))
    for i, m in enumerate(matrices):
        loc, rot, scale = (base_inverse @ m).decompose()
        axis, angle = rot.to_axis_angle()
        pos[i], axes[i], angles[i], scales[i] = loc, axis, angle, scale
    return pos, axes, angles, scales
