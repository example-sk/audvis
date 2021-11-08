import bpy

def _input(node, name, default_value, type="an_FloatSocket"):
    node.newInputSocket(type)
    socket = node.inputs[-2]  # TODO: find better way, -2 is very bad
    socket.text = name
    socket.value = default_value
    return socket


def make_nodes(context):
    node_tree = context.getActiveAnimationNodeTree()
    text_block = bpy.data.texts.new(name="audvis-an.py")
    text_block.write(_create_script(context))
    script = node_tree.nodes.new(type="an_ScriptNode")
    script.textBlock = text_block
    script.subprogramName = "audvis"
    script.label = "AudVis Script"
    script.newOutputSocket("an_FloatSocket")
    output_socket = script.outputs[-2]
    output_socket.text = "out"

    _input(node=script, name="index", default_value=0, type="an_IntegerSocket")
    _input(node=script, name="freq_start", default_value=0)
    _input(node=script, name="freq_range", default_value=50)
    _input(node=script, name="freq_step", default_value=50)
    _input(node=script, name="factor", default_value=1)

    subprogram = node_tree.nodes.new(type="an_InvokeSubprogramNode")
    subprogram.subprogramIdentifier = script.identifier
    subprogram.location[1] += 300
    subprogram.label = "AudVis Subprogram"


def _create_script(context):
    text = """
driver = bpy.app.driver_namespace['audvis']
out = factor * (driver(index * freq_step + freq_start, index * freq_step + freq_range + freq_start))
"""
    return text
