from . import (
    all,
    realtime,
    recording,
    video,
)

classes = [
    all.AUDVIS_OT_InstallAll,
    realtime.AUDVIS_OT_RealtimeUninstall,
    recording.AUDVIS_OT_RealtimeUninstallSoundRecorder,
    video.AUDVIS_OT_VideoUninstall,
]
