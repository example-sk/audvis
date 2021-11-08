import bpy


class AudvisSequenceProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable Audio Visualizer", default=True)
