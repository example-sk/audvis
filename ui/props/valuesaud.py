import bpy

from ...analyzer.analyzer import make_fake_curve_light


class AudvisValuesAudProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Use Better Filters")
    highpass: bpy.props.FloatProperty(name="Highpass Frequency", default=0, min=0)
    highpass_factor: bpy.props.FloatProperty(name="Q", default=.5, min=0.00001, max=1)
    lowpass: bpy.props.FloatProperty(name="Lowpass Frequency", default=100000, min=0)
    lowpass_factor: bpy.props.FloatProperty(name="Q", default=.5, min=0.00001, max=1)
    fake_curve_light: bpy.props.PointerProperty(type=bpy.types.Light, name="Fake Curve Light")
    use_fake_curve_light: bpy.props.BoolProperty(name="Use Curve", default=False, update=make_fake_curve_light,
                                                 description="Caution: this is quite slow")
    # aud.ADSR params
    adsr_enable: bpy.props.BoolProperty(name="ADSR", default=True)
    adsr_attack: bpy.props.FloatProperty(name="Attack", default=0.1, min=0, precision=3, step=1)
    adsr_decay: bpy.props.FloatProperty(name="Decay", default=0.01, min=0, precision=3, step=1)
    adsr_sustain: bpy.props.FloatProperty(name="Sustain", min=0, precision=3, step=1)
    adsr_release: bpy.props.FloatProperty(name="Release", default=0.200, min=0, precision=3, step=1)
    # aud.envelope params
    env_enable: bpy.props.BoolProperty(name="Envelope", default=False)
    env_attack: bpy.props.FloatProperty(name="Attack", default=0.005, min=0, precision=3)
    env_release: bpy.props.FloatProperty(name="Release", min=0, default=.2)
    env_threshold: bpy.props.FloatProperty(name="Threshold", min=0, default=0)
    env_arthreshold: bpy.props.FloatProperty(name="Attack/Release Threshold", default=0.100, min=0)
