import sys

if 'bge' in sys.modules:
    from .bge_midi import MidiRealtime
    from .bge_realtime import Realtime
    from .bge_updater import Updater
