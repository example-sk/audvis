from . import (
    spectrogram,
    animationnodes,
    valuesaud,
    spreaddrivers,
    scene,
    sequence,
    shapemodifier,
    armaturegenerator,
    party,
    obj,
    midi,
    daw_arrangement, realtimeprops,
)

classes = [
              animationnodes.AudvisAnimationnodesProperties,
              valuesaud.AudvisValuesAudProperties,
              party.AudvisPartyProperties,
          ] + midi.classes + daw_arrangement.classes + realtimeprops.classes + [
              spectrogram.AudvisSpectrogramProperties,
              spectrogram.AudvisSpectrogramMetaProperties,
              spreaddrivers.AudvisSceneSpreaddriversProperties,
              scene.AudvisSceneProperties,  # all prop groups in scene need to be above this line
              sequence.AudvisSequenceProperties,
              shapemodifier.AudvisObjectShapemodifierProperties,
              armaturegenerator.AudvisObjectArmatureGeneratorProperties,
              obj.AudvisObjectProperties,
          ]
