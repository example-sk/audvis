def _input(node, name, default_value, type="an_FloatSocket"):
    node.newInputSocket(type)
    socket = node.inputs[-2]  # TODO: find better way, -2 is very bad
    socket.name = name
    socket.text = name
    socket.value = default_value
    return socket


def _inputNode(node, name, default_value, index):
    sock = _input(node, name, default_value)
    input_node = node.nodeTree.nodes.new(type='an_DataInputNode')
    input_node.outputs[0].linkWith(sock)
    input_node.location[0] -= 200
    input_node.location[1] -= index * 80
    input_node.inputs[0].value = default_value
    return sock


def make_nodes(context):
    node_tree = context.getActiveAnimationNodeTree()
    expr_node = node_tree.nodes.new(type="an_ExpressionNode")
    expr_node.expression = "bpy.app.driver_namespace['audvis'](freq_from, freq_to) * factor"

    _inputNode(expr_node, 'freq_from', default_value=0, index=0)
    _inputNode(expr_node, 'freq_to', default_value=100, index=1)
    _inputNode(expr_node, 'factor', default_value=1, index=2)

    # expr_node.outputs[0].dataType = "an_FloatSocket"
