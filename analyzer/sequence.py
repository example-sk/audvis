import bpy
import os

from .analyzer import Analyzer


class _chunk:
    data = None
    time_from = -1
    time_to = -1


class SequenceAnalyzer(Analyzer):
    audio = None
    sequence = None
    sequence_name = None
    whole_data = None
    chunk = None
    load_error = None

    def load(self, sequence=None):
        if self.load_error is not None:
            return
        self.whole_data = _chunk()
        self.chunk = _chunk()
        if sequence is None:
            return
        self.sequence_name = sequence.name
        # print('AudVis loading', sequence.name)
        self.sequence = sequence

        depsgraph = bpy.context.evaluated_depsgraph_get()
        if sequence.sound.packed_file is not None or os.path.exists(bpy.path.abspath(sequence.sound.filepath)):
            self.audio = sequence.sound.evaluated_get(depsgraph).factory
            self.samplerate = self.audio.specs[0]
            scene = bpy.context.scene
            self.on_pre_frame(scene, scene.frame_current_final)
        else:
            self.load_error = FileNotFoundError("sound file does not exist")
            return

    def on_pre_frame(self, scene, frame):
        if self.sequence not in scene.sequence_editor.sequences_all.values():  # pointer to sequence changes after any undo in Blender
            if self.sequence_name in scene.sequence_editor.sequences_all:
                self.sequence = scene.sequence_editor.sequences_all[self.sequence_name]  # try to fix missing sequence
            else:
                self.empty()
                return
        self.sequence_name = self.sequence.name
        if frame < self.sequence.frame_final_start or frame > self.sequence.frame_final_end:
            self.empty()
            return
        if not self.audio:
            return

        fps = scene.render.fps / scene.render.fps_base

        time_to = scene.audvis.sequence_offset / 1000 + (
                frame
                - self.sequence.frame_final_start
                + self.sequence.frame_offset_start
                + self.sequence.animation_offset_start
        ) / fps
        time_from = time_to - scene.audvis.sample_calc
        if scene.audvis.sequence_chunks:
            self._check_chunk(time_from, time_to)
            chunk = self.chunk
        else:
            if self.whole_data.data is None:
                self._load_whole_sound()
            chunk = self.whole_data
        soundframe_from = (time_from - chunk.time_from) * self.samplerate
        soundframe_from = max(0, soundframe_from)
        soundframe_to = (time_to - chunk.time_from) * self.samplerate
        soundframe_to = max(0, soundframe_to)
        row = chunk.data[int(soundframe_from):int(soundframe_to)]
        self.lastdata = row
        self.calculate_fft()

    def _load_whole_sound(self):
        self.whole_data.data = self.audio.data()
        self.whole_data.time_from = 0
        self.whole_data.time_to = self.audio.length / self.samplerate

    def _check_chunk(self, time_from, time_to):
        if self.chunk.data is not None \
                and max(0, time_from) >= self.chunk.time_from \
                and time_to <= self.chunk.time_to:
            return
        time_from = max(0, time_from)
        time_to = max(time_from, time_to + 10)
        # print("AAAAAAA", self.audio.length)
        self.chunk.data = self.audio.limit(time_from, time_to).data()
        self.chunk.time_from = time_from
        self.chunk.time_to = time_to
        # print("AudVis chunk", time_from, time_to)

    def stop(self):
        self.empty()
        self.audio = None
        self.sequence = None
