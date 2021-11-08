import bpy


class AUDVIS_OT_BgeRegisterComponent(bpy.types.Operator):
    bl_idname = "audvis.bge_register_component"
    bl_label = "Register AudVis Component"

    component: bpy.props.StringProperty(name="Component", default="")

    @classmethod
    def poll(cls, context):
        return len(dir(bpy.ops.logic)) \
               and bpy.ops.logic.python_component_register.poll() \
               and bpy.ops.object.game_property_new.poll()

    def execute(self, context):
        bpy.ops.logic.python_component_register(component_name=self.component)
        if self.component != 'audvis.bge.Updater':
            bpy.ops.object.game_property_new(type='FLOAT', name="audvis_value")
            context.object.game.components[-1].properties['property_name'].value = context.object.game.properties[
                -1].name
        return {"FINISHED"}
