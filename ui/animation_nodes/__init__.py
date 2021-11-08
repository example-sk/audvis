import bpy

from . import (expression, script)


class AUDVIS_PT_animationnodes(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "AudVis"
    # bl_options = {'DEFAULT_CLOSED'}
    bl_label = 'AudVis'

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "getActiveAnimationNodeTree"):
            return False
        if context.getActiveAnimationNodeTree() is None:
            return False
        return True

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(context.scene.audvis.animation_nodes, "type")
        col.operator(AUDVIS_OT_animationnodesMakeNodes.bl_idname)
        if bpy.ops.audvis.animationnodes_fixparticlesdataoutputs.poll():
            col = self.layout.column(align=True)
            col.operator(bpy.ops.audvis.animationnodes_fixparticlesdataoutputs.bl_idname)


class AUDVIS_OT_animationnodesMakeNodes(bpy.types.Operator):
    bl_label = "Create AudVis Script Node"
    bl_idname = "audvis.animationnodes_makenodes"

    @classmethod
    def poll(cls, context):
        return AUDVIS_PT_animationnodes.poll(context)

    def _unselect_all(self, node_tree):
        for node in node_tree.nodes:
            node.select = False

    def execute(self, context):
        node_tree = context.getActiveAnimationNodeTree()
        self._unselect_all(node_tree)
        type = context.scene.audvis.animation_nodes.type
        if type == 'script':
            script.make_nodes(context)
        elif type == 'expression':
            expression.make_nodes(context)
        bpy.ops.node.translate_attach('INVOKE_DEFAULT')
        return {'FINISHED'}


classes = [
    AUDVIS_PT_animationnodes,
    AUDVIS_OT_animationnodesMakeNodes,
]
