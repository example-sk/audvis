import math

import bpy

from .midi import AudvisMidiGeneratorsProperties
from .. import motion
from ...analyzer.motion.audio import EQ_EDGES


class AudvisMotionAudioProperties(bpy.types.PropertyGroup):
    source: bpy.props.EnumProperty(name="Audio Source", default='sound', items=[
        ('off', "Off", "No sound - use only keyframed / manual values"),
        ('sound', "Sound", "Frequency range of the sound analyzers"),
        ('midi', "MIDI", "MIDI note"),
    ])
    spread: bpy.props.EnumProperty(name="Spread", default='same', items=[
        ('same', "Same for All", "Every element reacts to the same frequency range"),
        ('bands', "Frequency Bands", "Each element gets its own frequency range (or MIDI note)"),
        ('delay', "Time Delay", "Each element reacts later than the previous one - a wave travels through"),
    ])
    stereo: bpy.props.EnumProperty(name="Stereo", default='off', items=[
        ('off', "Off", "Use the Sound Channel only"),
        ('split', "Left / Right Halves", "First half of the elements follows Sound Channel (left), the second"
                                         " half the next channel (right). Scatter: pieces on -X / +X side"),
        ('alternate', "Alternate", "Every other element follows the right channel"),
    ], description="Needs Channels Count 2+ in the main AudVis panel")
    response: bpy.props.EnumProperty(name="Response", default='follow', items=[
        ('follow', "Follow", "Follow the loudness (smoothed by Attack / Release)"),
        ('trigger', "Beat Trigger", "Fire a one-shot envelope (0..1) when the sound crosses the Threshold"),
    ])
    threshold: bpy.props.FloatProperty(name="Threshold", default=.5, min=0, soft_max=5,
                                       description="Value (after Sensitivity) that fires a trigger")
    trigger_length: bpy.props.IntProperty(name="Length (frames)", default=24, min=1, soft_max=250)
    trigger_shape: bpy.props.EnumProperty(name="Shape", default='decay', items=[
        ('decay', "Hit & Decay", "Jump to 1, fade out"),
        ('pulse', "Pulse", "Rise and fall back (smooth there-and-back)"),
        ('hold', "Hold", "Stay at 1, drop at the end"),
    ])
    cooldown: bpy.props.IntProperty(name="Cooldown (frames)", default=6, min=0, soft_max=100,
                                    description="Minimum frames between two triggers")
    eq_band: bpy.props.EnumProperty(name="EQ Band", default='off', items=[
        ('off', "Off", "Use Frequency Start / Range below"),
    ] + [(str(i), "Band {} ({:g}-{:g} Hz)".format(i, EQ_EDGES[i - 1], EQ_EDGES[i]),
          "Use this band's frequency range and its gain from the EQ / Macros panel") for i in range(1, 9)])
    freq_start: bpy.props.FloatProperty(name="Frequency Start", default=20, min=0)
    freq_width: bpy.props.FloatProperty(name="Frequency Range", default=150, min=.01)
    freq_step: bpy.props.FloatProperty(name="Frequency Step", default=100, min=0,
                                       description="With Frequency Bands: distance between bands of two elements")
    delay: bpy.props.IntProperty(name="Delay (frames)", default=2, min=0, soft_max=30)
    midi_note: bpy.props.IntProperty(name="MIDI Note", default=36, min=0, max=127)
    midi: bpy.props.PointerProperty(name="MIDI", type=AudvisMidiGeneratorsProperties)
    channel: bpy.props.IntProperty(name="Sound Channel", default=1, min=1, soft_max=32)
    sound_sequence: bpy.props.StringProperty(name="Sequence", default="")
    sequence_channel: bpy.props.IntProperty(name="Sequence Channel", default=0, min=0,
                                            description="Channel number in Video Sequence Editor")
    factor: bpy.props.FloatProperty(name="Sensitivity", default=.1, min=0, soft_max=2, precision=3,
                                    description="Multiply the analyzer value. Effects expect values around 0..1")
    attack: bpy.props.FloatProperty(name="Attack", default=1, min=.01, max=1, subtype='FACTOR',
                                    description="How fast values rise (1 = immediately)")
    release: bpy.props.FloatProperty(name="Release", default=.15, min=.01, max=1, subtype='FACTOR',
                                     description="How fast values fall back (lower = slower, floatier)")


_INFLUENCE = "Fade the whole effect in / out"
CC_TARGETS = {  # stored by position: only append new targets
    'cascade': [('reveal', "Reveal", ""), ('spread', "Spread", "Multiplies offset / spacing"),
                ('twist', "Twist", "Multiplies the rotation"), ('influence', "Influence", _INFLUENCE)],
    'scatter': [('amount', "Amount", ""), ('morph', "Morph", ""), ('distance', "Distance", "Multiplies distance"),
                ('influence', "Influence", _INFLUENCE)],
    'orbit': [('gravity', "Gravity", ""), ('radius', "Orbit Radius", "Multiplies the orbit radius"),
              ('sphere', "Sphere Radius", "Multiplies the gravity sphere radius"), ('influence', "Influence", _INFLUENCE)],
    'attractor': [('strength', "Strength", "")],
}


def cc_target_items(self, context):
    path = self.path_from_id()
    for key, items in CC_TARGETS.items():
        if ".{}.".format(key) in path:
            return items
    return [('none', "None", "")]


class AudvisMotionCCProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="MIDI CC Control", default=False,
                                   description="Control a value live by a MIDI controller knob / fader."
                                               " Needs MIDI Realtime enabled")
    target: bpy.props.EnumProperty(name="Controls", items=cc_target_items)
    control: bpy.props.IntProperty(name="CC Number", default=1, min=0, max=127)
    channel: bpy.props.IntProperty(name="MIDI Channel", default=-1, min=-1, max=16, description="-1 = any")
    mode: bpy.props.EnumProperty(name="Mode", default='replace', items=[
        ('replace', "Replace", "The knob sets the value: Min .. Max"),
        ('add', "Add", "The knob adds Min .. Max"),
        ('multiply', "Multiply", "The knob multiplies by Min .. Max"),
    ])
    range_min: bpy.props.FloatProperty(name="Min", default=0)
    range_max: bpy.props.FloatProperty(name="Max", default=1)
    is_learning: bpy.props.BoolProperty(default=False)


class AudvisMotionAttractorProperties(bpy.types.PropertyGroup):
    mode: bpy.props.EnumProperty(name="Mode", default='attract', items=[
        ('attract', "Attract", "Pull onto a sphere around this object"),
        ('repel', "Repel", "Push away"),
        ('vortex', "Vortex", "Swirl around this object's Z axis"),
    ])
    strength: bpy.props.FloatProperty(name="Strength", default=1, soft_min=0, soft_max=1,
                                      description="Keyframe it. Attract: 1 = fully on the sphere")
    sphere_radius: bpy.props.FloatProperty(name="Sphere Radius", default=1, min=0, subtype='DISTANCE')
    distance: bpy.props.FloatProperty(name="Push Distance", default=2, soft_min=0, soft_max=20, subtype='DISTANCE')
    twist: bpy.props.FloatProperty(name="Twist (turns)", default=.25, soft_min=-2, soft_max=2)
    influence: bpy.props.FloatProperty(name="Influence Radius", default=0, min=0, subtype='DISTANCE',
                                       description="Full effect inside, fading out until twice the radius."
                                                   " 0 = everywhere")
    audio: bpy.props.PointerProperty(type=AudvisMotionAudioProperties)
    audio_strength: bpy.props.FloatProperty(name="Sound → Strength", default=1, soft_min=-2, soft_max=2)
    cc: bpy.props.PointerProperty(type=AudvisMotionCCProperties)


_OUTPUT_ITEMS = [
    ('objects', "Objects", "Separate objects - can be edited, baked, have their own materials"),
    ('instances', "Instances (fast)", "Geometry Nodes instances on one point cloud object. For thousands of"
                                      " elements"),
]


class AudvisMotionCascadeProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable Cascade", default=False, update=motion.effect_enable_update)
    influence: bpy.props.FloatProperty(name="Influence", default=1, min=0, max=1, subtype='FACTOR',
                                       description="How much the effect overrides the objects' own animation."
                                                   " 0 = they play their keyframes as if AudVis wasn't there."
                                                   " Keyframe it, or map a MIDI knob")
    is_baking: bpy.props.BoolProperty(default=False)
    output: bpy.props.EnumProperty(name="Output", items=_OUTPUT_ITEMS)
    collection: bpy.props.PointerProperty(name="Copies", type=bpy.types.Collection)
    instancer: bpy.props.PointerProperty(name="Instancer", type=bpy.types.Object)
    count: bpy.props.IntProperty(name="Copies", default=12, min=1, soft_max=200)
    linked: bpy.props.BoolProperty(name="Linked Data", default=True,
                                   description="Copies share the mesh/curve data with the source")
    layout: bpy.props.EnumProperty(name="Layout", default='chain', items=[
        ('chain', "Chain", "Each copy steps from the previous one - spirals, helixes, tunnels"),
        ('phyllotaxis', "Phyllotaxis", "Sunflower spiral (golden angle). Offset Z raises it into a cone"),
        ('grid', "Grid", "Columns x rows x layers"),
        ('curve', "Along Curve", "Spread along the first spline of a curve object"),
    ])
    spacing: bpy.props.FloatProperty(name="Spacing", default=.5, soft_min=0, soft_max=10, subtype='DISTANCE')
    grid_columns: bpy.props.IntProperty(name="Columns", default=8, min=1)
    grid_rows: bpy.props.IntProperty(name="Rows", default=8, min=1)
    curve_object: bpy.props.PointerProperty(name="Curve", type=bpy.types.Object,
                                            poll=lambda self, obj: obj.type == 'CURVE')
    curve_offset: bpy.props.FloatProperty(name="Curve Offset", default=0, soft_min=-1, soft_max=1,
                                          description="Slide along the curve. Keyframe it to make the copies flow")
    offset: bpy.props.FloatVectorProperty(name="Offset", default=(0, 0, .5), subtype='TRANSLATION',
                                          description="Each copy moves this much from the previous one")
    rotation: bpy.props.FloatVectorProperty(name="Rotation", default=(0, 0, math.radians(15)),
                                            subtype='EULER', description="Added to each copy")
    scale_step: bpy.props.FloatVectorProperty(name="Scale", default=(.95, .95, .95), min=.01, soft_max=2,
                                              subtype='XYZ', description="Multiplied for each copy")
    audio: bpy.props.PointerProperty(type=AudvisMotionAudioProperties)
    audio_offset: bpy.props.FloatProperty(name="Sound → Offset", default=1, soft_min=-5, soft_max=5,
                                          description="Sound stretches the offset step / spacing")
    audio_rotation: bpy.props.FloatProperty(name="Sound → Rotation", default=0, soft_min=-5, soft_max=5,
                                            description="Sound twists the rotation step")
    audio_scale: bpy.props.FloatProperty(name="Sound → Pulse", default=0, soft_min=-2, soft_max=5,
                                         description="Sound scales each copy (doesn't compound)")
    reveal: bpy.props.FloatProperty(name="Reveal", default=1, min=0, max=1, subtype='FACTOR',
                                    description="Show copies one after another. Keyframe it for a build-up")
    audio_reveal: bpy.props.FloatProperty(name="Sound → Reveal", default=0, soft_min=-2, soft_max=2,
                                          description="Sound of the first copy adds to Reveal")
    use_color: bpy.props.BoolProperty(name="Color Gradient", default=False,
                                      description="Set Object Color of the copies (Object Info > Color in shaders,"
                                                  " Viewport Shading > Color > Object). Instances: attribute"
                                                  " 'audvis_color' (Attribute node, type Instancer)")
    hue: bpy.props.FloatProperty(name="Hue", default=0, min=0, max=1, subtype='FACTOR')
    hue_step: bpy.props.FloatProperty(name="Hue Step", default=.04, soft_min=-.2, soft_max=.2)
    hue_speed: bpy.props.FloatProperty(name="Hue Cycle Speed", default=0, soft_min=-1, soft_max=1,
                                       description="Hue rotations per second")
    saturation: bpy.props.FloatProperty(name="Saturation", default=.8, min=0, max=1, subtype='FACTOR')
    audio_hue: bpy.props.FloatProperty(name="Sound → Hue", default=0, soft_min=-1, soft_max=1)
    attractors: bpy.props.PointerProperty(name="Attractors", type=bpy.types.Collection)
    cc: bpy.props.PointerProperty(type=AudvisMotionCCProperties)


class AudvisMotionScatterProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable Scatter", default=False, update=motion.scatter_enable_update)
    influence: bpy.props.FloatProperty(name="Influence", default=1, min=0, max=1, subtype='FACTOR',
                                       description="How much the effect scatters the mesh."
                                                   " 0 = assembled shape."
                                                   " Keyframe it, or map a MIDI knob")
    original_mesh: bpy.props.PointerProperty(name="Original Mesh", type=bpy.types.Mesh)
    prepared_id: bpy.props.IntProperty(default=0)
    prepared_mode: bpy.props.StringProperty(default="")
    piece_mode: bpy.props.EnumProperty(name="Tear Into", default='faces', items=[
        ('faces', "Faces", "Every face becomes a separate shard (Grease Pencil: every stroke)"),
        ('islands', "Loose Parts", "Every loose part (mesh island) moves as one piece (Grease Pencil: stroke)"),
        ('vertices', "Vertices", "Every vertex / point moves alone - faces and strokes stretch like a web"),
    ])
    seed: bpy.props.IntProperty(name="Seed", default=1)
    style: bpy.props.EnumProperty(name="Style", default='explode', items=[
        ('explode', "Explode", "Pieces fly out along a direction and come back - scrubbable"),
        ('fluid', "Fluid", "Pieces drift in a Navier-Stokes flow stirred by the sound."
                           " Simulated frame by frame: play from the start"),
    ])
    amount: bpy.props.FloatProperty(name="Amount", default=0, min=0, max=1, subtype='FACTOR',
                                    description="0 = assembled, 1 = fully scattered. Fluid: how hard the flow"
                                                " is stirred. Keyframe it")
    fluid_resolution: bpy.props.IntProperty(name="Resolution", default=24, min=8, soft_max=40, max=64,
                                            description="Fluid grid cells per side. Higher = finer swirls,"
                                                        " slower (24: ~10 ms per frame)")
    fluid_domain: bpy.props.FloatProperty(name="Domain Size", default=3, min=1.2, soft_max=8,
                                          description="Size of the fluid box around the object (x object size)")
    fluid_burst: bpy.props.FloatProperty(name="Sound Burst", default=6, soft_min=-20, soft_max=30,
                                         description="Sound pushes the fluid out from the center"
                                                     " (negative: sucks it in)")
    fluid_swirl: bpy.props.FloatProperty(name="Swirl", default=2, soft_min=-10, soft_max=10,
                                         description="Stir around the Z axis, harder with the sound")
    fluid_turbulence: bpy.props.FloatProperty(name="Turbulence", default=2, min=0, soft_max=20,
                                              description="Random swirly currents (curl noise)")
    fluid_turbulence_scale: bpy.props.FloatProperty(name="Turbulence Scale", default=2, min=.1, soft_max=8,
                                                    description="Higher = smaller eddies")
    fluid_turbulence_speed: bpy.props.FloatProperty(name="Turbulence Speed", default=.3, min=0, soft_max=3,
                                                    description="How fast the currents change")
    fluid_audio_turbulence: bpy.props.FloatProperty(name="Sound → Turbulence", default=2, soft_min=0, soft_max=10)
    fluid_vorticity: bpy.props.FloatProperty(name="Vorticity", default=2, min=0, soft_max=20,
                                             description="Keep small swirls alive and spinning (vorticity"
                                                         " confinement). High = wild, curly flow")
    fluid_audio_vorticity: bpy.props.FloatProperty(name="Sound → Vorticity", default=0, soft_min=0, soft_max=10)
    fluid_viscosity: bpy.props.FloatProperty(name="Viscosity", default=.05, min=0, max=1, subtype='FACTOR',
                                             description="Thick, smooth flow (honey) vs thin and chaotic (smoke)")
    fluid_damping: bpy.props.FloatProperty(name="Damping", default=2, min=0, soft_max=10,
                                           description="The flow calms down by itself (per second)")
    fluid_buoyancy: bpy.props.FloatProperty(name="Buoyancy", default=0, soft_min=-5, soft_max=5,
                                            description="Rise (smoke) or sink")
    fluid_follow: bpy.props.FloatProperty(name="Follow", default=.7, min=0, max=1, subtype='FACTOR',
                                          description="1 = pieces float exactly with the fluid,"
                                                      " lower = heavier pieces that lag behind")
    fluid_spin: bpy.props.FloatProperty(name="Spin", default=1, min=0, soft_max=5,
                                        description="Pieces turn with the swirls of the flow")
    fluid_return: bpy.props.FloatProperty(name="Return", default=.3, min=0, soft_max=3,
                                          description="Pull the pieces back into shape (or into the Morph"
                                                      " Target). 0 = they drift away for good")
    fluid_keep_on_loop: bpy.props.BoolProperty(name="Keep Flowing on Loop", default=True,
                                               description="When playback loops back to the start, keep the"
                                                           " flow going instead of snapping back together")
    audio: bpy.props.PointerProperty(type=AudvisMotionAudioProperties)
    audio_amount: bpy.props.FloatProperty(name="Sound → Amount", default=1, soft_min=-2, soft_max=2)
    audio_elements: bpy.props.IntProperty(name="Bands / Delay Steps", default=8, min=1, soft_max=64,
                                          description="With Frequency Bands or Time Delay: pieces are split into"
                                                      " this many groups by the Stagger order")
    distance: bpy.props.FloatProperty(name="Distance", default=2, soft_min=0, soft_max=20, subtype='DISTANCE')
    distance_random: bpy.props.FloatProperty(name="Distance Random", default=.5, min=0, max=1, subtype='FACTOR')
    direction: bpy.props.EnumProperty(name="Direction", default='outward', items=[
        ('outward', "Outward", "Away from the object origin"),
        ('normal', "Face Normal", "Along the piece's normal"),
        ('random', "Random", ""),
        ('vector', "Vector", "Every piece flies the same direction"),
    ])
    direction_vector: bpy.props.FloatVectorProperty(name="Vector", default=(0, 0, 1), subtype='XYZ')
    direction_random: bpy.props.FloatProperty(name="Direction Random", default=.2, min=0, max=1, subtype='FACTOR')
    rotation: bpy.props.FloatProperty(name="Tumble", default=180, soft_min=0, soft_max=720,
                                      description="Max rotation of a piece when fully scattered (degrees)")
    tumble_speed: bpy.props.FloatProperty(name="Tumble Speed", default=0, soft_min=0, soft_max=2,
                                          description="Keep rotating while scattered (turns per second)")
    shrink: bpy.props.FloatProperty(name="Shrink", default=0, min=0, max=1, subtype='FACTOR')
    turbulence: bpy.props.FloatProperty(name="Turbulence", default=0, min=0, soft_max=2, subtype='DISTANCE',
                                        description="Pieces float around while scattered")
    turbulence_speed: bpy.props.FloatProperty(name="Turbulence Speed", default=.5, min=0, soft_max=4)
    orbit_speed: bpy.props.FloatProperty(name="Orbit Speed", default=0, soft_min=-1, soft_max=1,
                                         description="Scattered pieces circle the object's origin (turns per"
                                                     " second). Amount 0 still snaps them back together")
    orbit_tilt: bpy.props.FloatProperty(name="Orbit Tilt", default=.2, min=0, soft_max=3,
                                        description="0 = flat ring around Z, higher = tilted orbits, swarm")
    stagger: bpy.props.FloatProperty(name="Stagger", default=0, min=0, soft_max=4,
                                     description="Pieces leave one after another instead of all together")
    stagger_mode: bpy.props.EnumProperty(name="Stagger Order", default='distance', items=[
        ('distance', "Distance", "Inner pieces first"),
        ('z', "Height", "Bottom pieces first"),
        ('random', "Random", ""),
    ])
    stagger_invert: bpy.props.BoolProperty(name="Invert Order", default=False)
    morph_target: bpy.props.PointerProperty(name="Morph Target", type=bpy.types.Object,
                                            poll=lambda self, obj: obj.type == 'MESH' and obj != self.id_data,
                                            description="Mesh whose shape the pieces rebuild at Morph 1")
    morph: bpy.props.FloatProperty(name="Morph", default=0, min=0, max=1, subtype='FACTOR',
                                   description="0 = own shape, 1 = shape of the Morph Target. Keyframe it")
    audio_morph: bpy.props.FloatProperty(name="Sound → Morph", default=0, soft_min=-2, soft_max=2)
    morph_scatter: bpy.props.FloatProperty(name="Fly While Morphing", default=.5, min=0, max=1, subtype='FACTOR',
                                           description="How far the pieces scatter on their way to the target")
    morph_scale: bpy.props.FloatProperty(name="Piece Size at Target", default=1, min=.01, soft_max=3,
                                         description="Pieces are scaled to cover the target's area; tweak here")
    attractors: bpy.props.PointerProperty(name="Attractors", type=bpy.types.Collection,
                                          description="Attractors move only loose pieces")
    cc: bpy.props.PointerProperty(type=AudvisMotionCCProperties)


class AudvisMotionOrbitProperties(bpy.types.PropertyGroup):
    enable: bpy.props.BoolProperty(name="Enable Orbit", default=False, update=motion.effect_enable_update)
    influence: bpy.props.FloatProperty(name="Influence", default=1, min=0, max=1, subtype='FACTOR',
                                       description="How much the effect overrides the objects' own animation."
                                                   " 0 = they play their keyframes as if AudVis wasn't there."
                                                   " Keyframe it, or map a MIDI knob")
    is_baking: bpy.props.BoolProperty(default=False)
    output: bpy.props.EnumProperty(name="Output", items=_OUTPUT_ITEMS)
    collection: bpy.props.PointerProperty(name="Satellites", type=bpy.types.Collection,
                                          description="Objects orbiting this object")
    instancer: bpy.props.PointerProperty(name="Instancer", type=bpy.types.Object)
    source_object: bpy.props.PointerProperty(name="Satellite Object", type=bpy.types.Object,
                                             description="Copied by Populate. Empty = small ico spheres")
    count: bpy.props.IntProperty(name="Count", default=40, min=1, soft_max=2000)
    seed: bpy.props.IntProperty(name="Seed", default=1)
    radius_min: bpy.props.FloatProperty(name="Radius Min", default=2, min=.01, subtype='DISTANCE')
    radius_max: bpy.props.FloatProperty(name="Radius Max", default=5, min=.01, subtype='DISTANCE')
    inclination: bpy.props.FloatProperty(name="Inclination", default=25, min=0, max=180,
                                         description="Max tilt of the orbits (degrees). 90+ = spherical swarm")
    speed: bpy.props.FloatProperty(name="Speed", default=.1, soft_min=-2, soft_max=2,
                                   description="Turns per second of the innermost orbit")
    kepler: bpy.props.BoolProperty(name="Kepler Speeds", default=True,
                                   description="Outer orbits are slower, like planets")
    scale: bpy.props.FloatProperty(name="Scale", default=1, min=0, soft_max=5)
    scale_random: bpy.props.FloatProperty(name="Scale Random", default=.3, min=0, max=1, subtype='FACTOR')
    align: bpy.props.EnumProperty(name="Rotation", default='spin', items=[
        ('spin', "Spin", "Rotate around a random axis"),
        ('tangent', "Follow Orbit", "Face the flight direction"),
        ('none', "None", ""),
    ])
    spin_speed: bpy.props.FloatProperty(name="Spin Speed", default=.25, soft_min=-2, soft_max=2)
    audio: bpy.props.PointerProperty(type=AudvisMotionAudioProperties)
    audio_speed: bpy.props.FloatProperty(name="Sound → Speed", default=.5, soft_min=-5, soft_max=5,
                                         description="Sound pushes the orbits forward")
    audio_radius: bpy.props.FloatProperty(name="Sound → Radius", default=0, soft_min=-1, soft_max=2,
                                          description="Sound pushes satellites outward")
    gravity: bpy.props.FloatProperty(name="Gravity", default=0, min=0, max=1, subtype='FACTOR',
                                     description="Pull the satellites onto the gravity sphere. Keyframe it")
    audio_gravity: bpy.props.FloatProperty(name="Sound → Gravity", default=0, soft_min=-2, soft_max=2)
    gravity_mode: bpy.props.EnumProperty(name="Gravity Shape", default='shell', items=[
        ('shell', "Sphere Shell", "Satellites spread evenly over the sphere surface"),
        ('radial', "Radial", "Satellites fall straight down onto the sphere"),
        ('core', "Core", "Satellites are swallowed by the center and shrink"),
    ])
    sphere_radius: bpy.props.FloatProperty(name="Sphere Radius", default=1, min=0, subtype='DISTANCE',
                                           update=motion.orbit_sphere_update)
    show_sphere: bpy.props.BoolProperty(name="Show Sphere", default=True, update=motion.orbit_sphere_update,
                                        description="If the center is an Empty, display it as the gravity sphere")
    gravity_stagger: bpy.props.FloatProperty(name="Gravity Stagger", default=.5, min=0, soft_max=4,
                                             description="Outer satellites arrive later")
    shell_spin: bpy.props.FloatProperty(name="Shell Spin", default=.05, soft_min=-1, soft_max=1,
                                        description="Turns per second of the sphere shell")
    attractors: bpy.props.PointerProperty(name="Attractors", type=bpy.types.Collection)
    cc: bpy.props.PointerProperty(type=AudvisMotionCCProperties)


def _refresh_on_change(cls):
    """Give every property without its own update callback motion.refresh, so the
    viewport follows the sliders while the animation is paused."""
    skip = {'is_baking', 'prepared_id', 'prepared_mode', 'original_mesh', 'instancer', 'is_learning'}
    for name, prop in cls.__annotations__.items():
        if name not in skip and 'update' not in prop.keywords:
            cls.__annotations__[name] = prop.function(**prop.keywords, update=motion.refresh)
    return cls


classes = [_refresh_on_change(cls) for cls in [
    AudvisMotionAudioProperties,
    AudvisMotionCCProperties,
    AudvisMotionAttractorProperties,
    AudvisMotionCascadeProperties,
    AudvisMotionScatterProperties,
    AudvisMotionOrbitProperties,
]]
