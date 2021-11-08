import bpy


class AUDVIS_OT_BgeLogicCreate(bpy.types.Operator):
    bl_idname = "audvis.bge_logic_create"
    bl_label = "Create Action Logic"

    @classmethod
    def poll(cls, context):
        return len(dir(bpy.ops.logic)) \
               and bpy.ops.logic.sensor_add.poll()

    def execute(self, context):
        obj = context.object
        bpy.ops.logic.sensor_add(type='ALWAYS', name="always audvis")
        sensor = obj.game.sensors[-1]
        sensor.use_pulse_true_level = True

        bpy.ops.logic.controller_add(type='LOGIC_AND', name="and audvis", object="")
        controller = obj.game.controllers[-1]

        bpy.ops.logic.actuator_add(type='ACTION', name="action audvis")
        actuator = context.object.game.actuators[-1]

        controller.link(sensor=sensor)
        controller.link(actuator=actuator)
        if obj.animation_data:
            actuator.action = obj.animation_data.action
        actuator.play_mode = 'PROPERTY'

        return {"FINISHED"}
