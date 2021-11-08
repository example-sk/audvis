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
)

classes = [
              animationnodes.AudvisAnimationnodesProperties,
              valuesaud.AudvisValuesAudProperties,
              party.AudvisPartyProperties,
          ] + midi.classes + [
              spectrogram.AudvisSpectrogramProperties,
              spreaddrivers.AudvisSceneSpreaddriversProperties,
              scene.AudvisSceneProperties,  # all prop groups in scene need to be above this line
              sequence.AudvisSequenceProperties,
              shapemodifier.AudvisObjectShapemodifierProperties,
              armaturegenerator.AudvisObjectArmatureGeneratorProperties,
              obj.AudvisObjectProperties,
          ]
