import bpy

from ..buttonspanel import AudVisButtonsPanel_Npanel

_is_baking = False


# TODO: self.report({'INFO'},"This ma take some time")

# TODO: subframes
class DriverBakery:
    list = []

    def prepare(self, context):
        self.list = []
        self._find_drivers()
        self._find_nodetree_drivers()

    def _find_drivers(self):
        traverse_list = [
            # look the part "References" on the bottom of https://docs.blender.org/api/master/bpy.types.AnimData.html
            bpy.data.armatures,
            # CacheFile, # TODO: do we have something with this?
            bpy.data.cameras,
            bpy.data.curves,
            # FreestyleLineStyle,
            bpy.data.grease_pencils,
            bpy.data.shape_keys,
            bpy.data.lattices,
            bpy.data.lights,
            bpy.data.lightprobes,
            bpy.data.masks,
            bpy.data.materials,
            bpy.data.meshes,
            bpy.data.metaballs,
            bpy.data.movieclips,
            # bpy.data.NodeTree,
            bpy.data.objects,
            bpy.data.particles,
            bpy.data.pointclouds,
            bpy.data.scenes,
            bpy.data.speakers,
            bpy.data.textures,
            bpy.data.worlds,
            bpy.data.node_groups,
            # TODO: make this list complete
        ]
        if hasattr(bpy.data, "volumes"):
            traverse_list.append(bpy.data.volumes)
        for traverse in traverse_list:
            for obj in traverse:
                self._add_if_driver(obj)

    def _find_nodetree_drivers(self):
        nodetrees_traverse_list = [
            # https://docs.blender.org/api/blender2.8/search.html?q=node_tree&check_keywords=yes&area=default
            bpy.data.lights,
            bpy.data.materials,
            bpy.data.textures,
            bpy.data.scenes,
            bpy.data.worlds,
        ]
        # objects with "node_tree"
        for lst in nodetrees_traverse_list:
            for el in lst:
                if el.node_tree is not None:
                    self._add_if_driver(el.node_tree)

    def clear_drivers(self):
        for el, path, array_index in self.list:
            el.driver_remove(path, array_index)

    def bake(self):
        # audvis.audvis.update_data(context.scene)
        for el, path, array_index in self.list:
            # TODO: how to check if use array_index? try:except is just a horrible override
            try:
                el.keyframe_insert(path, index=array_index)
            except:
                try:
                    el.keyframe_insert(path)
                except:
                    # drivers for deleted properties probably
                    pass

    def _add_if_driver(self, el):
        animdata = el.animation_data
        if animdata is None:
            return
        if animdata.drivers is None:
            return
        for fcurve in animdata.drivers:
            if fcurve.driver is None:
                continue
            if fcurve.driver.type != 'SCRIPTED':
                continue
            if "audvis(" not in fcurve.driver.expression:
                continue
            self.list.append([
                el,
                fcurve.data_path,
                fcurve.array_index
            ])


class AUDVIS_OT_BakeDrivers(bpy.types.Operator):
    bl_idname = "audvis.bakedrivers"
    bl_label = "Bake Drivers"

    return_frame = -1
    cur_frame = -1
    end_frame = -1
    timer = None
    bakery = None

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        global _is_baking
        bpy.ops.screen.animation_cancel()
        scene = context.scene
        self.return_frame = scene.frame_current
        self.cur_frame = scene.frame_start
        self.end_frame = scene.frame_end
        context.scene.frame_set(self.cur_frame)
        self.timer = context.window_manager.event_timer_add(.0000001, window=context.window)
        self.bakery = DriverBakery()
        self.bakery.prepare(context)
        # context.window_manager.progress_begin(scene.frame_start, scene.frame_end)
        context.workspace.status_text_set("AudVis: Baking Drivers")
        context.window_manager.modal_handler_add(self)
        _is_baking = True
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            context.scene.frame_set(self.cur_frame)
            # context.window_manager.progress_update(self.cur_frame)
            start = context.scene.frame_start
            perc = int(((self.cur_frame - start) / (self.end_frame - start)) * 100)
            context.workspace.status_text_set("AudVis: Baking Drivers: {}%".format(perc))
            self.bakery.bake()
            if self.cur_frame >= self.end_frame:
                self.bakery.clear_drivers()
                self._end(context)
                return {'FINISHED'}
            self.cur_frame += 1
            return {'PASS_THROUGH'}
        elif event.type == 'ESC':
            self._end(context)
            return {'FINISHED'}
        return {'PASS_THROUGH'}

    def _end(self, context):
        global _is_baking
        context.scene.frame_set(self.return_frame)
        context.workspace.status_text_set(None)
        _is_baking = False


class AUDVIS_PT_BakeDriversNpanel(AudVisButtonsPanel_Npanel):
    bl_label = "Bake Drivers"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        global _is_baking
        col = self.layout.column(align=True)
        col.label(text="Warning: this can take")
        col.label(text="a very long time")
        col.label(text="and it's inreversible.")
        col.label(text="Please make a backup")
        col.label(text="before doing this")
        col = self.layout.column(align=True)
        if _is_baking:
            col.label(text="Baking drivers.")
            col.label(text="Press ESC to cancel")
        else:
            col.operator("audvis.bakedrivers")

        col = self.layout.column(align=True)
        col.label(text="Nonstop Baking Collection:")
        col.prop(context.scene.audvis, "nonstop_baking_collection", text="")
        col.prop(context.scene.audvis, "nonstop_baking_editexpressions")
        if context.scene.audvis.nonstop_baking_collection is not None and context.scene.audvis.nonstop_baking_editexpressions:
            for obj in context.scene.audvis.nonstop_baking_collection.all_objects:
                animdata = obj.animation_data
                if animdata is not None:
                    if animdata.drivers is not None and len(animdata.drivers):
                        col.label(text=obj.name)
                        box = col.box()
                        for fcurve in animdata.drivers:
                            if fcurve.driver is not None:
                                box.label(text="%s [%d]" % (fcurve.data_path, fcurve.array_index))
                                box.prop(fcurve.driver, "expression", text="")


classes = [
    AUDVIS_OT_BakeDrivers,
    AUDVIS_PT_BakeDriversNpanel,
]
