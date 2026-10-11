import bpy

from . import (
    armaturegenerator,
    motion,
    shapemodifier,
)


class AudvisObjectProperties(bpy.types.PropertyGroup):
    shapemodifier: bpy.props.PointerProperty(type=shapemodifier.AudvisObjectShapemodifierProperties)
    armature_generator: bpy.props.PointerProperty(type=armaturegenerator.AudvisObjectArmatureGeneratorProperties)
    cascade: bpy.props.PointerProperty(type=motion.AudvisMotionCascadeProperties)
    scatter: bpy.props.PointerProperty(type=motion.AudvisMotionScatterProperties)
    orbit: bpy.props.PointerProperty(type=motion.AudvisMotionOrbitProperties)
    attractor: bpy.props.PointerProperty(type=motion.AudvisMotionAttractorProperties)
