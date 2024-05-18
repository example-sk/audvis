from bpy.types import Panel


class AudVisButtonsPanel_Npanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AudVis"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        pass


class SequencerButtonsPanel_Update:
    """Use for subpanels"""
    pass
