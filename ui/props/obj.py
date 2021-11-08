import bpy

from . import (
    armaturegenerator,
    shapemodifier,
)


class AudvisObjectProperties(bpy.types.PropertyGroup):
    shapemodifier: bpy.props.PointerProperty(type=shapemodifier.AudvisObjectShapemodifierProperties)
    armature_generator: bpy.props.PointerProperty(type=armaturegenerator.AudvisObjectArmatureGeneratorProperties)
