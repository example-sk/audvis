import bpy
from bpy.types import (
    Operator,
)


def _get_spect_props(context):
    if context.scene.audvis.spectrogram_meta.mode == 'single':
        return context.scene.audvis.spectrogram
    else:
        if context.scene.audvis.spectrogram_meta.index < len(context.scene.audvis.spectrograms):
            return context.scene.audvis.spectrograms[context.scene.audvis.spectrogram_meta.index]


class AUDVIS_OT_spectrogramMakeParticles(Operator):
    bl_idname = "audvis.spectrogram_make_particles"
    bl_label = "Make Particle System"

    @classmethod
    def poll(cls, context):
        if not context.object or context.object.type not in ('MESH',):
            return False
        if not bpy.ops.object.particle_system_add.poll():
            return False
        if context.scene.audvis.spectrogram_meta.mode != 'multi':
            return False
        return True

    def execute(self, context):
        bpy.ops.audvis.spectrogram_add()
        spect_props = context.scene.audvis.spectrograms[-1]
        spect_props.mode = 'one-big'
        spect_props.width = 1
        bpy.ops.object.particle_system_add()
        psystem = context.object.particle_systems[-1]

        psettings = psystem.settings
        psystem.name = 'audvis'
        psettings.name = 'audvis'
        psettings.count = 3003
        psettings.frame_start = context.scene.frame_start
        psettings.frame_end = context.scene.frame_end
        psettings.render_type = 'OBJECT'
        slot = psettings.texture_slots.add()
        slot.texture = bpy.data.textures.new(name='audvis', type='IMAGE')
        slot.texture.extension = 'EXTEND'
        slot.texture.image = spect_props.image
        slot.use_map_time = False
        slot.use_map_size = True
        slot.texture_coords = 'STRAND'
        bpy.ops.mesh.primitive_cube_add(location=(0, 10, 0))
        render_obj = bpy.context.object
        psettings.instance_object = render_obj
        return {'FINISHED'}
