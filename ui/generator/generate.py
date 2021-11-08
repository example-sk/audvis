import math
import random

import bmesh
import bpy

from . import material
from ...note_calculator import calculate_note


def build_expression(freq_from, freq_to, conf, factor=None):
    ch = conf.example_channel
    add = conf.example_driver_add
    if factor is None:
        factor = conf.example_driver_factor
    kwargs = ""
    if ch != 1:
        kwargs += ", ch=%i" % ch
    if conf.example_sound_sequence:
        kwargs += ", seq=" + repr(conf.example_sound_sequence)
    expr = "audvis({}, {}{})".format(freq_from, freq_to, kwargs)
    if factor is not None and factor != 1:
        expr += " * {}".format(factor)
    if add != 0.0:
        expr += " + {}".format(add)
    return expr


class Generator:
    add_kwargs = ""

    def __init__(self, context):
        self.context = context
        self.scene = context.scene
        self.conf = self.scene.audvis
        self.range = 0
        self.is_280 = hasattr(bpy.data, "collections")

    def _clean_collection(self, collection):
        for obj in collection.objects:
            collection.objects.unlink(obj)

    def _make_collections(self):
        bpy.ops.object.select_all(action='DESELECT')
        coll_action = self.conf.example_collections_action
        reuse_coll = None
        reuse_subcoll = None
        for collection in self.scene.collection.children:
            if collection.name.startswith("AudVisExample"):
                if coll_action == 'reuse':
                    for child in collection.children:
                        if child.name.startswith("AudVisExampleRanges"):
                            reuse_subcoll = child
                    reuse_coll = collection
                elif coll_action == 'remove+new':
                    self.scene.collection.children.unlink(collection)
        bpy.ops.object.delete(confirm=False)

        if coll_action == 'remove+new' or coll_action == 'keep+new' or reuse_coll is None or reuse_subcoll is None:
            collection = bpy.data.collections.new("AudVisExample")
            subcollection = bpy.data.collections.new("AudVisExampleRanges")
        if reuse_coll is not None and reuse_subcoll is not None:
            collection = reuse_coll
            subcollection = reuse_subcoll
            self._clean_collection(collection)
            self._clean_collection(subcollection)
        else:
            self.scene.collection.children.link(collection)
            collection.children.link(subcollection)

        self.collection = collection
        self.subcollection = subcollection
        return collection, subcollection

    def _make_groups(self):
        group_action = self.conf.example_collections_action
        reuse_group = None
        reuse_subgroup = None
        for group in bpy.data.groups:
            if group.name.startswith("AudVisExample"):
                if group.name.startswith("AudVisExampleRanges") and group_action == 'reuse':
                    reuse_subgroup = group
                    for obj in group.objects:
                        bpy.context.scene.objects.unlink(obj)
                elif group_action == 'reuse':
                    reuse_group = group
                    for obj in group.objects:
                        bpy.context.scene.objects.unlink(obj)
                elif group_action == 'remove+new':
                    for obj in group.objects:
                        bpy.context.scene.objects.unlink(obj)
                    bpy.data.groups.remove(group)
        # bpy.ops.object.delete(confirm=False)  # wtf?

        if group_action == 'remove+new' or group_action == 'keep+new' or reuse_group is None or reuse_subgroup is None:
            group = bpy.data.groups.new("AudVisExample")
            subgroup = bpy.data.groups.new("AudVisExampleRanges")
        if reuse_group is not None and reuse_subgroup is not None:
            group = reuse_group
            subgroup = reuse_subgroup
            self._clean_collection(group)
            self._clean_collection(subgroup)

        self.group = group
        self.subgroup = subgroup
        return group, subgroup

    def generate(self):
        xcount = self.conf.example_xcount
        ycount = self.conf.example_ycount
        zcount = self.conf.example_zcount
        self.size = self.conf.example_width / max(xcount, ycount, zcount)

        if self.is_280:
            collection, subcollection = self._make_collections()
        else:
            group, subgroup = self._make_groups()
        lattice = None
        empty = None
        if self.conf.example_lattice:
            lattice = self.make_lattice()
            self.obj_add_to_group(lattice)
        if self.conf.example_empty:
            empty = bpy.data.objects.new('AudVisExampleEmpty', None)
            if hasattr(empty, "empty_display_type"):  # blender 2.80
                empty.empty_display_type = 'SPHERE'
            if lattice is not None:
                lattice.location = (0, 0, 0)
                lattice.parent = empty
            self.obj_add_to_group(empty)

        mat = None
        if self.scene.audvis.example_material == 'One':
            mat = material.generate_material(self.scene.audvis, 0, 1000)
        rangeperobject = self.conf.example_rangeperobject
        freqstart = self.conf.example_freqstart
        template_obj = None
        if self.conf.example_object_type == 'Select Object:':
            template_obj = self.conf.example_object
            if template_obj is None:
                return {'CANCELLED'}
        elif self.conf.example_object_type == 'Select From Collection:':
            pass
        else:
            template_obj = self.create_object()
            template_obj.name = "AudVisExample Template"
            if mat is not None:
                template_obj.data.materials.append(mat)
            template_obj.location = (self.conf.example_width * 2 + 1, 0, 0)
            self.obj_add_to_group(template_obj)
        add = (0, 0, 0)
        if empty is None:
            add = self.scene.cursor.location
        total_num = zcount * xcount * ycount
        if self.conf.example_freq_step_enable:
            freq_step = self.conf.example_freq_step
        else:
            freq_step = rangeperobject
        index = -1
        for k in range(zcount):
            for i in range(xcount):
                for j in range(ycount):
                    index += 1
                    if self.conf.example_object_type == 'Random From Collection:':
                        sel_collection = self.conf.example_collection
                        if sel_collection is None or len(sel_collection.objects) == 0:
                            return {'CANCELLED'}
                        template_obj = random.choice(sel_collection.objects)
                    if self.conf.example_freq_seq_type == 'notes':
                        freq_from = calculate_note((index + self.conf.example_note_offset) * self.conf.example_note_step, self.conf.example_note_a4_freq)
                        freq_to = calculate_note((index + self.conf.example_note_offset + 1) * self.conf.example_note_step, self.conf.example_note_a4_freq)
                        freq_from = round(freq_from * 100) / 100
                        freq_to = round(freq_to * 100) / 100
                    else:
                        freq_from = index * freq_step + freqstart
                        freq_to = freq_from + rangeperobject
                    obj = template_obj.copy()
                    for modifier in obj.modifiers:  # quickfix for bug https://developer.blender.org/T71604
                        if modifier.type == 'CLOTH':
                            template_cloth_modifier = template_obj.modifiers[modifier.name]
                            modifier.point_cache.frame_start = template_cloth_modifier.point_cache.frame_start
                            modifier.point_cache.frame_end = template_cloth_modifier.point_cache.frame_end
                            modifier.point_cache.frame_step = template_cloth_modifier.point_cache.frame_step
                            modifier.point_cache.use_disk_cache = template_cloth_modifier.point_cache.use_disk_cache
                            modifier.point_cache.use_library_path = template_cloth_modifier.point_cache.use_library_path
                    if obj.type == 'META':
                        pass  # just keep the name
                    else:
                        objname = ("AudVisExample_%dhz-%dhz" % (freq_from, freq_to))
                        obj.name = objname

                    if self.conf.example_randomize_location:
                        obj.location = (
                            self.conf.example_width * random.random() - self.conf.example_width / 2,
                            self.conf.example_width * random.random() - self.conf.example_width / 2,
                            self.conf.example_width * random.random() - self.conf.example_width / 2,
                        )
                    elif self.conf.example_shape == 'circle':
                        step = self.conf.example_width - self.conf.example_circle_radius
                        step /= 2
                        if ycount > 1:
                            step /= ycount - 1
                        obj.location = (
                            math.sin((i / xcount) * math.pi * 2) * (self.conf.example_width / 2 - step * j),
                            math.cos((i / xcount) * math.pi * 2) * (self.conf.example_width / 2 - step * j),
                            add[2] + self.size * k - ((zcount - 1) / 2) * self.size,
                        )
                        obj.rotation_euler[2] = math.atan2(obj.location[1], obj.location[0])
                    else:
                        obj.location = (
                            add[0] + self.size * i - ((xcount - 1) / 2) * self.size,
                            add[1] + self.size * j - ((ycount - 1) / 2) * self.size,
                            add[2] + self.size * k - ((zcount - 1) / 2) * self.size,
                        )
                    if self.conf.example_shape == 'curve' and self.conf.example_curve_object:
                        self._curve_this(obj, (i, j, k), (xcount, ycount, zcount))
                    if self.conf.example_randomize_rotation:
                        obj.rotation_euler = (
                            (1 - random.random() * self.conf.example_randomize_rotation) * math.pi * 2,
                            (1 - random.random() * self.conf.example_randomize_rotation) * math.pi * 2,
                            (1 - random.random() * self.conf.example_randomize_rotation) * math.pi * 2,
                        )
                    if self.conf.example_objectsize_type == 'relative':
                        scale = self.size / 2 * self.conf.example_objectsize
                        scale *= 1 - self.conf.example_randomize_scale * random.random()
                        obj.scale = (
                            scale,
                            scale,
                            scale,
                        )
                    elif self.conf.example_objectsize_type == 'fixed':
                        obj.scale = self.conf.example_objectsize_fixed_value

                    if self.scene.audvis.example_material in ['Many', 'Copy+Modify']:
                        material_many = material.generate_material(self.scene.audvis, freq_from, freq_to)
                        obj.data = obj.data.copy()
                        obj.data.materials.append(material_many)

                    self.add_drivers_to_obj(obj, freq_from, freq_to)
                    if empty is not None:
                        obj.parent = empty
                    if lattice is not None:
                        try:
                            obj.modifiers.new('', 'LATTICE').object = lattice
                        except:
                            pass
                    self.obj_add_to_group(obj, True)
                    self.range += rangeperobject

    def _curve_this(self, object, xyz, cnt_xyz):
        axis = self.conf.example_curve_axis
        constraint = object.constraints.new(type='FOLLOW_PATH')
        constraint.target = self.conf.example_curve_object
        constraint.use_curve_follow = True
        constraint.forward_axis = axis
        if axis[-1] == 'X':
            index = 0
        elif axis[-1] == 'Y':
            index = 1
        elif axis[-1] == 'Z':
            index = 2
        object.location[index] = 0
        constraint.offset = -(xyz[index] / cnt_xyz[index]) * 100

    def _copy_data_if_driver_and_animdata(self, obj):
        if not hasattr(obj.data, "animation_data") or obj.data.animation_data is None:
            return False
        if self.conf.example_object.data is not obj.data:
            return True
        for fcurve in obj.data.animation_data.drivers:
            if "audvis()" in fcurve.driver.expression:
                obj.data = obj.data.copy()
                return True
        return False

    def _float_to_str(self, num, precision=6):
        val = ("%." + str(precision) + "f") % (num)
        return val.rstrip("0").rstrip(".")

    def add_drivers_to_obj(self, obj, freq_from, freq_to):
        expr = build_expression(freq_from, freq_to, self.conf)
        if self.conf.example_driver_objectdrivers and self.conf.example_object_type == 'Select Object:' and obj.animation_data is not None:
            for fcurve in obj.animation_data.drivers:
                if fcurve.driver and "audvis()" in fcurve.driver.expression:
                    fcurve.driver.expression = fcurve.driver.expression.replace("audvis()", "(%s)" % expr)
        if self.conf.example_driver_objectdrivers and self.conf.example_object_type == 'Select Object:' and self._copy_data_if_driver_and_animdata(
                obj):
            for fcurve in obj.data.animation_data.drivers:
                if fcurve.driver and "audvis()" in fcurve.driver.expression:
                    fcurve.driver.expression = fcurve.driver.expression.replace("audvis()", "(%s)" % expr)

        if self.conf.example_objectsize_type == 'relative':
            s = self.size / 2 * self.conf.example_driver_factor
            scale = (s, s, s)
        elif self.conf.example_objectsize_type == 'fixed':
            scale = (
                self.conf.example_objectsize_fixed_value[0],
                self.conf.example_objectsize_fixed_value[1],
                self.conf.example_objectsize_fixed_value[2],
            )
        else:  # should never happen
            print("AudVis: the value of example_objectsize_type is weird")
            scale = (1, 1, 1)
        if self.conf.example_driver_scalex:
            d = obj.driver_add("scale", 0)
            d.driver.expression = build_expression(freq_from, freq_to, self.conf, factor=scale[0])
        if self.conf.example_driver_scaley:
            d = obj.driver_add("scale", 1)
            d.driver.expression = build_expression(freq_from, freq_to, self.conf, factor=scale[1])
        if self.conf.example_driver_scalez:
            d = obj.driver_add("scale", 2)
            d.driver.expression = build_expression(freq_from, freq_to, self.conf, factor=scale[2])

        expr = build_expression(freq_from, freq_to, self.conf, factor=self.size / 2 * self.conf.example_driver_factor)
        if self.conf.example_driver_locx:
            d = obj.driver_add("location", 0)
            d.driver.expression = expr + (" + %f" % (obj.location[0]))
        if self.conf.example_driver_locy:
            d = obj.driver_add("location", 1)
            d.driver.expression = expr + (" + %f" % (obj.location[1]))
        if self.conf.example_driver_locz:
            d = obj.driver_add("location", 2)
            d.driver.expression = expr + (" + %f" % (obj.location[2]))

        expr = build_expression(freq_from, freq_to, self.conf)
        if self.conf.example_driver_rotx:
            d = obj.driver_add("rotation_euler", 0)
            d.driver.expression = expr + (" + %f" % (obj.rotation_euler[0]))
        if self.conf.example_driver_roty:
            d = obj.driver_add("rotation_euler", 1)
            d.driver.expression = expr + (" + %f" % (obj.rotation_euler[1]))
        if self.conf.example_driver_rotz:
            d = obj.driver_add("rotation_euler", 2)
            d.driver.expression = expr + (" + %f" % (obj.rotation_euler[2]))

    def make_lattice(self):
        lattice = bpy.data.lattices.new("AudVisExampleLattice")
        lattice.points_u = 5
        lattice.points_v = 5
        lattice.points_w = 5
        lattice = bpy.data.objects.new("AudVisExampleLattice", lattice)
        lattice.data.use_outside = True
        override = {
            'window': self.context.window,
            'screen': self.context.screen,
            'area': self.context.area,
            'object': lattice,
        }
        bpy.ops.object.shape_key_add(override)
        bpy.ops.object.shape_key_add(override)
        d = lattice.active_shape_key.driver_add('value')
        d.driver.expression = 'audvis(10,1000)/10'
        lattice.scale = (
            self.conf.example_width / 4, self.conf.example_width / 4, self.conf.example_width / 4)
        return lattice

    def obj_add_to_group(self, obj, sub=False):
        if self.is_280:
            if not sub:
                self.collection.objects.link(obj)
            else:
                self.subcollection.objects.link(obj)
        else:
            if not obj.name in bpy.context.scene.objects:
                bpy.context.scene.objects.link(obj)
            if not sub:
                self.group.objects.link(obj)
            else:
                self.subgroup.objects.link(obj)

    def create_object(self):
        mesh_type = self.conf.example_object_type
        mesh = bpy.data.meshes.new("AudVisExampleObject")
        bm = bmesh.new()
        if mesh_type == 'Suzanne':
            bmesh.ops.create_monkey(bm)
        elif mesh_type == 'Cube':
            bmesh.ops.create_cube(bm, size=2.0)
        bm.to_mesh(mesh)
        bm.free()
        return bpy.data.objects.new("", mesh)
