# copied from space_sequencer.py
class SequencerButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        pass


class SequencerButtonsPanel_Npanel:
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
