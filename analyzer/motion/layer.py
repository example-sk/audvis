"""Override layer: Motion FX never writes the transform of the user's own objects.

Each user object an effect moves gets a Copy Transforms constraint ("AudVis Orbit (Center)")
targeting a hidden helper empty in the "AudVis Motion Layer" collection. The engine only moves
the helper and sets the constraint influence, so the object's own keyframes, drivers and
transform stay untouched: influence 1 overrides them, 0 shows them exactly as before.
Constraints are evaluated after the animation, in the viewport and in final renders.

Objects AudVis generated itself (cascade copies, satellites) have no animation of their own
and are placed directly; at influence < 1 they shrink away instead.
"""
import bpy
from mathutils import Matrix

from .lib import HELPER_KEY, INDEX_KEY, place as place_directly

COLLECTION = "AudVis Motion Layer"
LAYER_KEY = "audvis_motion_layer"  # on the collection
OWNER_KEY = "audvis_layer_owner"  # on helpers: name of the object owning the effect
EFFECT_KEY = "audvis_layer_effect"
BAKED_KEY = "audvis_layer_baked"
MIN_SCALE = 1e-4


def constraint_name(effect, owner_name):
    return "AudVis {} ({})".format(effect.title(), owner_name)


def is_generated(obj):
    return INDEX_KEY in obj


def _collection(scene):
    coll = next((c for c in bpy.data.collections if c.get(LAYER_KEY)), None)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION)
        coll[LAYER_KEY] = True
        coll.hide_viewport = coll.hide_render = True
    if scene.collection.children.get(coll.name) is None:
        scene.collection.children.link(coll)  # helpers must be linked somewhere or saving drops them
    return coll


def _layer_target(con):
    target = con.target if con.type == 'COPY_TRANSFORMS' else None
    return target if target is not None and OWNER_KEY in target else None


def _ensure(obj, effect, owner, scene):
    name = constraint_name(effect, owner.name)
    con = obj.constraints.get(name)
    if con is not None and _layer_target(con) is not None:
        return con
    if con is not None:
        obj.constraints.remove(con)
    helper = bpy.data.objects.new("{} > {}".format(name, obj.name), None)
    helper[HELPER_KEY] = True
    helper[OWNER_KEY] = owner.name
    helper[EFFECT_KEY] = effect
    helper.empty_display_size = .1
    helper.matrix_world = obj.matrix_world
    _collection(scene).objects.link(helper)
    con = obj.constraints.new('COPY_TRANSFORMS')
    con.name = name
    con.target = helper
    con.influence = 0.0
    return con


def _set_influence(con, value):
    if abs(con.influence - value) > 1e-6:  # don't re-tag the object every frame for nothing
        con.influence = value


def place(owner, effect, obj, matrix, frame, bake, influence, scene):
    """Move one element of an effect to matrix (world space), faded by influence (0..1)."""
    if is_generated(obj):
        if influence < 1:
            matrix = matrix @ Matrix.Scale(max(MIN_SCALE, influence), 4)
        place_directly(obj, matrix, frame, bake)
        return
    con = _ensure(obj, effect, owner, scene)
    helper = con.target
    if bake:
        helper[BAKED_KEY] = True
    elif helper.get(BAKED_KEY):  # going live again replaces the bake
        helper.animation_data_clear()
        del helper[BAKED_KEY]
    place_directly(helper, matrix, frame, bake)
    _set_influence(con, influence)


def sync(engine, owner, effect, objects):
    """Release objects that left the effect's collection since the last frame."""
    key = (owner.name, effect)
    names = {o.name for o in objects if not is_generated(o)}
    gone = engine.layer_members.get(key, set()) - names
    engine.layer_members[key] = names
    for name in gone:
        obj = bpy.data.objects.get(name)
        con = obj.constraints.get(constraint_name(effect, owner.name)) if obj is not None else None
        if con is not None and _layer_target(con) is not None:
            _set_influence(con, 0.0)


def constraints(scene, owner_name=None, effect=None):
    """(object, constraint) of the layer, optionally only one owner / effect."""
    for obj in scene.objects:
        for con in obj.constraints:
            target = _layer_target(con)
            if target is None:
                continue
            if owner_name is not None and target[OWNER_KEY] != owner_name:
                continue
            if effect is not None and target.get(EFFECT_KEY) != effect:
                continue
            yield obj, con


def release(scene, owner_name=None, effect=None):
    """Hand the objects back to their own animation (baked layers keep playing)."""
    for _, con in list(constraints(scene, owner_name, effect)):
        if not con.target.get(BAKED_KEY):
            _set_influence(con, 0.0)


def remove(scene, owner_name=None, effect=None):
    """Delete constraints and helpers - the objects are exactly as before AudVis touched them."""
    for obj, con in list(constraints(scene, owner_name, effect)):
        helper = con.target
        obj.constraints.remove(con)
        if helper is not None and helper.name in bpy.data.objects:
            bpy.data.objects.remove(helper, do_unlink=True)
    coll = next((c for c in bpy.data.collections if c.get(LAYER_KEY)), None)
    if coll is not None and owner_name is None and effect is None:
        for helper in list(coll.objects):  # orphans whose object was deleted
            bpy.data.objects.remove(helper, do_unlink=True)
    if coll is not None and not coll.objects:
        bpy.data.collections.remove(coll)


def summary(scene):
    """(overridden objects, baked objects) for the UI."""
    live = baked = 0
    for _, con in constraints(scene):
        if con.target.get(BAKED_KEY):
            baked += 1
        elif con.influence > 0:
            live += 1
    return live, baked
