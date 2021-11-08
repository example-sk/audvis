import os
import threading
import time

import bpy
import numpy as np

from . import video_to_object
from ..analyzer import Analyzer


def webcam_toggle_callback(props, context):
    from ... import audvis
    analyzer = audvis.get_video_analyzer(context.scene)
    if analyzer:
        analyzer.toggle_callback(context.scene)


class VideoThread(threading.Thread):
    current_camera_index = None
    requested_camera_index = None
    stream = None
    kill_me = False
    last_frame = None
    cv = None
    error = None
    force_reload = False
    lock = None

    def _restart_if_needed(self):
        if self.lock is None:
            self.lock = threading.Lock()
        req = self.requested_camera_index
        cur = self.current_camera_index
        if not self.force_reload and req == cur:
            return
        self.force_reload = False
        self.current_camera_index = req
        if self.stream is not None and self.stream.isOpened():
            self.stream.release()
            self.stream = None
        if req is None:
            return
        if self.cv is not None:
            self.stream = self.cv.VideoCapture(req)

    def run(self):
        while self._thread_continue():
            # print("vidwhile", time.time())
            try:
                self._restart_if_needed()
                if self.stream is not None and self.stream.isOpened():
                    if self.lock.locked():
                        time.sleep(.005)
                        continue
                    status, self.last_frame = self.stream.read()
                    if not status:
                        time.sleep(.2)
                else:
                    time.sleep(.2)
            except Exception as e:
                self.error = str(e)
                # print("AudVis", e)
                time.sleep(.5)
        if self.stream is not None and self.stream.isOpened():
            self.stream.release()

    def _thread_continue(self):
        if self.kill_me:
            return False
        if not threading.main_thread().is_alive():
            return False
        if not threading.current_thread().is_alive():
            return False
        return True


class VideoAnalyzer(Analyzer):
    status = 'init'
    supported = None
    stream = None
    cv = None
    error = None
    image = None
    updated = True
    thread = None
    last_saved_frame = None

    def load(self):
        try:
            import cv2
            self.cv = cv2
            self.supported = True
        except Exception as e:
            self.supported = False
            # print("AudVis", e)
            return
        scene = bpy.context.scene
        self.on_pre_frame(scene, bpy.context.scene.frame_current_final)

    def stop(self):
        if self.thread is not None:
            self.thread.requested_camera_index = None

    def kill(self):
        if self.thread is not None:
            self.thread.kill_me = True

    def toggle_callback(self, scene):
        self._load_stream(scene)

    def on_pre_frame(self, scene, frame):
        self._load_stream(scene)
        if scene.audvis.video_webcam_enable:
            self._read_synchronous(scene)

    def _load_stream(self, scene):
        if self.cv is None:
            return
        if self.thread is None:
            t = VideoThread(daemon=True)
            t.cv = self.cv
            t.start()
            self.thread = t
        if scene.audvis.video_webcam_enable:
            self.thread.requested_camera_index = scene.audvis.video_webcam_index
        else:
            self.thread.requested_camera_index = None

    def _read_synchronous(self, scene):
        try:
            if self.thread is not None:
                data = self.thread.last_frame
                if data is not None and data is not self.last_saved_frame:
                    tempdir = scene.audvis.video_tmppath
                    if tempdir == '':
                        tempdir = bpy.app.tempdir
                    filename = os.path.join(bpy.path.abspath(tempdir), "audvis.jpg")
                    self.last_saved_frame = data
                    try:
                        self.thread.lock.acquire(blocking=True, timeout=1)
                        if scene.audvis.video_resize:
                            width = scene.audvis.video_width
                            height = scene.audvis.video_height
                            if scene.audvis.video_resize_relative:
                                width = len(data[0]) * scene.audvis.video_resize_ratio
                                height = len(data) * scene.audvis.video_resize_ratio
                            width = max(1, width)
                            height = max(1, height)
                            data = self.cv.resize(data, (int(width), int(height)))
                        if scene.audvis.video_image_flip_horizontal:
                            data = np.fliplr(data)
                        self.cv.imwrite(filename, data)
                    finally:
                        self.thread.lock.release()
                    if scene.audvis.video_image is None:
                        scene.audvis.video_image = bpy.data.images.load(filename)
                    else:
                        img = scene.audvis.video_image
                        # without this hack, we have a pink material instead of image texture
                        if not len(img.pixels):
                            img.source = "GENERATED"
                            img.scale(100, 100)
                        img.source = "FILE"
                        # end of hack
                        img.filepath = filename
                    video_to_object.run(scene, self.cv)
                    self.error = None
        except Exception as e:
            self.error = str(e)
            # print("AudVis", e)
