"""Motion FX presets: starting points that set a handful of values and (re)build the effect."""
import math

import bpy

_DEG = math.radians

PRESETS = {
    'cascade': [
        ("dna", "DNA Helix", "Tall twisting chain, a wave travels up with the beat", {
            "layout": 'chain', "count": 60, "offset": (0, 0, .15), "rotation": (0, 0, _DEG(30)),
            "scale_step": (1, 1, 1), "audio_offset": .6, "audio_scale": .5, "audio.spread": 'delay',
            "audio.delay": 1, "use_color": True, "hue_step": .015, "reveal": 1,
        }),
        ("tunnel", "Tunnel", "Shrinking, rotating copies - fly through them", {
            "layout": 'chain', "count": 40, "offset": (0, .6, 0), "rotation": (0, _DEG(8), 0),
            "scale_step": (.94, .94, .94), "audio_offset": .3, "audio_rotation": 1.5,
            "audio.spread": 'bands', "audio.freq_step": 60, "reveal": 1,
        }),
        ("sunflower", "Sunflower", "Phyllotaxis disc, every seed has its own frequency band", {
            "layout": 'phyllotaxis', "count": 300, "spacing": .25, "offset": (0, 0, 0), "rotation": (0, 0, 0),
            "scale_step": (1, 1, 1), "audio_offset": 0, "audio_scale": 1.5, "audio.spread": 'bands',
            "audio.freq_step": 20, "use_color": True, "hue_step": .003, "reveal": 1,
        }),
        ("whip", "Whip", "Bending chain that lashes with a delay wave", {
            "layout": 'chain', "count": 30, "offset": (0, 0, .4), "rotation": (_DEG(6), 0, 0),
            "scale_step": (.98, .98, .98), "audio_offset": .2, "audio_rotation": 2.5, "audio.spread": 'delay',
            "audio.delay": 2, "reveal": 1,
        }),
        ("eq_grid", "Equalizer Grid", "8x8 grid of bars, one band each", {
            "layout": 'grid', "count": 63, "grid_columns": 8, "grid_rows": 8, "spacing": 1.2,
            "offset": (0, 0, 0), "rotation": (0, 0, 0), "scale_step": (1, 1, 1), "audio_offset": 0,
            "audio_scale": 2, "audio.spread": 'bands', "audio.freq_step": 60, "reveal": 1,
        }),
    ],
    'scatter': [
        ("supernova", "Supernova", "Explodes on every beat, falls back together", {
            "piece_mode": 'faces', "direction": 'outward', "distance": 6, "rotation": 360, "shrink": .3,
            "audio.response": 'trigger', "audio.trigger_shape": 'decay', "audio.trigger_length": 30,
            "audio.threshold": .4, "audio_amount": 1, "amount": 0, "stagger": 0,
        }),
        ("disintegrate", "Disintegrate", "Blows away bottom-up like ash. Keyframe Amount 0 → 1", {
            "piece_mode": 'faces', "direction": 'vector', "direction_vector": (0, 0, 1), "direction_random": .6,
            "distance": 4, "stagger": 2, "stagger_mode": 'z', "turbulence": .3, "shrink": .8,
            "audio.source": 'off', "amount": .5,
        }),
        ("breathing", "Breathing Shards", "Shards lift along their normals with the music", {
            "piece_mode": 'faces', "direction": 'normal', "direction_random": 0, "distance": .6,
            "rotation": 20, "turbulence": .05, "audio.response": 'follow', "audio.release": .05,
            "audio_amount": 1.5, "amount": 0,
        }),
        ("galaxy", "Galaxy Shards", "The shards circle the object like a ring galaxy", {
            "piece_mode": 'faces', "direction": 'outward', "distance": 3, "distance_random": 1,
            "orbit_speed": .15, "orbit_tilt": .15, "tumble_speed": .2, "amount": .8, "audio_amount": .2,
        }),
        ("core_skin", "Bass Core, Treble Skin", "Inner pieces follow the bass, outer ones the highs", {
            "piece_mode": 'faces', "audio.spread": 'bands', "audio_elements": 6, "audio.freq_start": 20,
            "audio.freq_step": 300, "stagger_mode": 'distance', "stagger": 0, "distance": 1.5,
            "audio_amount": 1.5, "amount": 0,
        }),
    ],
    'orbit': [
        ("ring_collapse", "Ring Collapse", "Flat ring, slams into a sphere on every beat", {
            "count": 150, "inclination": 2, "radius_min": 3, "radius_max": 6, "gravity_mode": 'shell',
            "gravity": 0, "audio_gravity": 1, "audio.response": 'trigger', "audio.trigger_shape": 'pulse',
            "audio.trigger_length": 40, "gravity_stagger": 1, "align": 'tangent',
        }),
        ("swarm", "Swarm", "Spherical swarm that breathes with the music", {
            "count": 300, "inclination": 180, "radius_min": 1.5, "radius_max": 4, "align": 'tangent',
            "audio_radius": .5, "speed": .2, "audio.response": 'follow',
        }),
        ("black_hole", "Black Hole", "Everything gets swallowed by the center on loud parts", {
            "count": 200, "inclination": 10, "speed": .3, "gravity_mode": 'core', "gravity": 0,
            "audio_gravity": 1, "audio.response": 'follow', "audio.release": .05, "gravity_stagger": 2,
        }),
        ("planets", "Planets", "A few big, slow, Kepler-correct planets", {
            "count": 12, "kepler": True, "scale": 1.5, "scale_random": .6, "inclination": 5,
            "radius_min": 2, "radius_max": 9, "speed": .05, "align": 'spin',
        }),
    ],
}


def preset_items(effect):
    return [(key, label, desc) for key, label, desc, _ in PRESETS[effect]]


BASELINE = {"audio.source": 'sound', "audio.response": 'follow', "audio.spread": 'same'}


def apply(settings, effect, key):
    for k, label, desc, values in PRESETS[effect]:
        if k == key:
            for path, value in {**BASELINE, **values}.items():
                owner = settings
                *parents, name = path.split(".")
                for parent in parents:
                    owner = getattr(owner, parent)
                setattr(owner, name, value)
            return label
    return None


class AUDVIS_OT_motionPreset(bpy.types.Operator):
    """Apply a Motion FX preset to the active object"""
    bl_idname = "audvis.motion_preset"
    bl_label = "Apply Motion FX Preset"
    bl_options = {'REGISTER', 'UNDO'}

    effect: bpy.props.StringProperty()
    preset: bpy.props.StringProperty()

    def execute(self, context):
        from . import motion
        obj = context.active_object or context.object
        if obj is None or self.effect not in PRESETS:
            return {'CANCELLED'}
        settings = getattr(obj.audvis, self.effect)
        if apply(settings, self.effect, self.preset) is None:
            return {'CANCELLED'}
        context.scene.audvis.motion_enable = True
        if self.effect == 'cascade':
            bpy.ops.audvis.motion_cascade_generate()
        elif self.effect == 'orbit':
            bpy.ops.audvis.motion_orbit_populate()
        elif obj.type in ('MESH', 'GREASEPENCIL'):
            if not motion.scatter_prepared(obj) or settings.prepared_mode != settings.piece_mode:
                bpy.ops.audvis.motion_scatter_prepare()
            settings.enable = True
        motion.refresh(context=context)
        return {'FINISHED'}


def _menu(effect, title):
    def draw(self, context):
        for key, label, desc, _ in PRESETS[effect]:
            op = self.layout.operator("audvis.motion_preset", text=label)
            op.effect = effect
            op.preset = key

    return type("AUDVIS_MT_motion_presets_" + effect, (bpy.types.Menu,), {
        "bl_idname": "AUDVIS_MT_motion_presets_" + effect,
        "bl_label": title,
        "draw": draw,
    })


menus = {effect: _menu(effect, effect.title() + " Presets") for effect in PRESETS}

classes = [AUDVIS_OT_motionPreset] + list(menus.values())
