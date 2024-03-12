import bpy

from ...note_calculator import calculate_note


def generate(context):
    obj = context.active_object or context.object
    props = obj.audvis.armature_generator
    if props.inset:
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.inset(thickness=props.inset_size, depth=0, use_individual=True)
        if props.inset_and_extrude:
            bpy.ops.mesh.extrude_region()
        props.inset = False
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    l = [p for p in obj.data.polygons if p.select]

    if not props.keep_old_vgroups:
        for g in obj.vertex_groups:
            if g.name.startswith("AudvisArm"):
                obj.vertex_groups.remove(g)

    bones_conf = []
    for p in l:
        vg = obj.vertex_groups.new(name="AudvisArm")
        vg.add(index=p.vertices, weight=1, type='ADD')
        bones_conf.append({
            "name": vg.name,
            "center": p.center,
            "normal": p.normal,
        })

    if props.armature_object and props.armature_object.type == 'ARMATURE' and props.armature_object.name in context.scene.objects:
        arm_object = props.armature_object
        bpy.context.view_layer.objects.active = arm_object
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        if not props.keep_old_vgroups:
            for b in list(arm_object.data.edit_bones):
                arm_object.data.edit_bones.remove(b)
    else:
        bpy.ops.object.add(type="ARMATURE", enter_editmode=True)
        arm_object = context.object
        arm_object.location = (0, 0, 0)
    arm_object.parent = obj
    props.armature_object = arm_object
    # arm_object.location = obj.location
    # arm_object.rotation_euler = obj.rotation_euler
    # arm_object.scale = obj.scale

    for bone_conf in bones_conf:
        bone = arm_object.data.edit_bones.new(name=bone_conf["name"])
        bone.head = bone_conf["center"]
        bone.tail = bone_conf["center"] + bone_conf["normal"] / 3
        # arm_object.pose.bones[bone.name]

    modifier_name = "AudVis Armature"
    if not props.keep_old_vgroups and modifier_name in obj.modifiers:
        modifier = obj.modifiers[modifier_name]
    else:
        modifier = obj.modifiers.new(name=modifier_name, type="ARMATURE")
    modifier.object = arm_object
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    index = 0
    rangeperobject = props.freqrange
    freqstart = props.freqstart
    if props.freq_step_enable:
        freq_step = props.freq_step
    else:
        freq_step = rangeperobject
    for bone_conf in bones_conf:
        pose_bone = arm_object.pose.bones[bone_conf["name"]]
        fcurve = pose_bone.driver_add("location", 1)
        if props.freq_seq_type == 'midi':
            expr_kwargs = 'midi={}'.format(index + props.midi.offset)
            if props.midi.file != '':
                expr_kwargs += ', file=' + repr(props.midi.file)
            if props.midi.track != '':
                expr_kwargs += ', track=' + repr(props.midi.track)
            if props.midi.channel != 'all' and props.midi.channel != '':
                expr_kwargs += ', ch=' + repr(props.midi.channel)
            if props.midi.device != '':
                expr_kwargs += ', device=' + repr(props.midi.device)
            fcurve.driver.expression = "audvis({}) * {:.6}".format(expr_kwargs, props.factor)
        else:
            expr_kwargs = ''
            if props.freq_seq_type == 'notes':
                freq_from = calculate_note((index + props.note_offset) * props.note_step,
                                           props.note_a4_freq)
                freq_to = calculate_note((index + props.note_offset + 1) * props.note_step,
                                         props.note_a4_freq)
                freq_from = round(freq_from * 100) / 100
                freq_to = round(freq_to * 100) / 100
            else:
                freq_from = index * freq_step + freqstart
                freq_to = freq_from + rangeperobject
            if props.sound_sequence != '':
                expr_kwargs += ', seq=' + repr(props.sound_sequence)
            if props.sequence_channel > 0:
                expr_kwargs +=', seq_channel=' + str(props.sequence_channel)
            if props.channel != 1:
                expr_kwargs += ', ch={}'.format(props.channel)
            fcurve.driver.expression = "audvis({}, {}{}) * {:.6}".format(freq_from, freq_to, expr_kwargs, props.factor)
        index += 1
    bpy.context.view_layer.objects.active = obj
