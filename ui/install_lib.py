import importlib
import os
import pathlib
import subprocess
import sys
import sysconfig
import threading
import time
from glob import glob
from queue import Queue

import bpy

if os.path.basename(sys.prefix).startswith("python") and os.path.isfile(sys.prefix):
    _python_path = sys.prefix
else:
    _python_path = glob(os.path.join(os.path.realpath(sys.prefix), 'bin', 'python*'))[0]
modules_path = bpy.utils.user_resource("SCRIPTS", path=os.path.join("addons", "modules"))
main_path = sysconfig.get_paths()['purelib']
audvis_libs_path = bpy.utils.user_resource("SCRIPTS", path=os.path.join("addons", "modules", "_audvis_modules"))


def get_libs_path_latest():
    search_path = os.path.join(audvis_libs_path, 'a_*')
    directories = glob(search_path)
    if len(directories):
        directories.sort(reverse=True)
        return directories[0]
    return None


def libs_path_mkdir():
    now = int(time.time())
    dir_path = os.path.join(audvis_libs_path, "a_" + str(now))
    pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)
    return dir_path


class _AsyncFileReader(threading.Thread):
    def __init__(self, fd):
        self.queue = Queue()
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd

    def run(self):
        for line in iter(self._fd.readline, ''):
            self.queue.put(line)

    def eof(self):
        return not self.is_alive() and self.queue.empty()


class PipInstaller(threading.Thread):
    process = None
    test = 1
    cb = None
    output_lines = None
    finished = False
    last_lines_num = 0

    def __init__(self):
        threading.Thread.__init__(self)
        self._selected_target = bpy.context.preferences.addons['audvis'].preferences.pip_target

    def run(self):
        self.cb()

    def bpy_tick(self):
        if self.last_lines_num < len(self.output_lines) or not self.is_alive():
            self.text_obj.clear()
            self.text_obj.write("")
            self.text_obj.write("".join(self.output_lines))
        if self.is_alive():
            bpy.app.timers.register(self.bpy_tick, first_interval=1)
        else:
            self.text_obj.write("\n\nFINISHED!\n")
            # TODO: return to preferences and show message
            # if originally was PREFRENCES:
            # bpy.ops.preferences.addon_show(module="audvis")
            self.text_obj.write("\n")
            if bpy.ops.screen.userpref_show.poll():
                bpy.ops.preferences.addon_show(module="audvis")
            else:  # dirty fix for blender 2.83 and lower
                self.text_obj.write("Now you can close this window\n")
            self.text_obj.write('\n"""')
            self.reload_libs()

    def reload_libs(self):
        importlib.invalidate_caches()
        audvis = sys.modules['audvis'].audvis
        if audvis.is_realtime_supported(force=True):
            analyzer = audvis.realtime_analyzer
            if analyzer is not None:
                analyzer.load()
        if audvis.is_video_supported(force=True):
            analyzer = audvis.video_analyzer
            if analyzer is not None:
                analyzer.load()
        if audvis.is_midi_realtime_supported(force=True):
            analyzer = audvis.midi_realtime_analyzer
            if analyzer is not None:
                analyzer.load()
        if audvis.is_recording_supported(force=True):
            pass  # TODO

    def _open_window(self):
        context = bpy.context
        # bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        bpy.ops.wm.window_new()
        window = context.window_manager.windows[-1]
        # override = {'window': window, 'screen': window.screen, 'area': window.screen.areas[0]}
        override = {
            'screen': window.screen,
            'area': window.screen.areas[0],
        }
        override['area'].type = 'TEXT_EDITOR'
        space = override['area'].spaces[0]
        space.text = self.text_obj
        if hasattr(context, 'temp_override'): # blender 3.2 or higher
            with context.temp_override(**override):
                bpy.ops.screen.screen_full_area()
        else: # blender 3.1 or lower
            bpy.ops.screen.screen_full_area(override)

    def install(self):
        self.output_lines = ['"""']
        self.text_obj = bpy.data.texts.new(name="audvis-install.log")
        self._open_window()
        bpy.app.timers.register(self.bpy_tick, first_interval=1)
        self.cb = self._install_all
        self.start()

    def _ensure_pip(self):
        add_params = []
        if self._selected_target in ['addon-modules']:
            add_params = ['--user']
        self._run_command([_python_path, '-m', 'ensurepip', '--altinstall'] + add_params)
        self._run_command(
            [
                _python_path,
                '-m',
                'pip',
                'install',
                '--upgrade',
                'pip'
            ] + add_params)

    def uninstall(self, package):
        self.output_lines = ['"""']
        self.text_obj = bpy.data.texts.new(name="audvis-install.log")
        self._open_window()
        bpy.app.timers.register(self.bpy_tick, first_interval=1)
        if package == "all":
            self.cb = self._uninstall_all
        elif package == "recorder":
            self.cb = self._uninstall_recorder
        elif package == "sd":
            self.cb = self._uninstall_sounddevice
        elif package == "cv2":
            self.cb = self._uninstall_video
        self.start()

    def _uninstall_all(self):
        self._uninstall_sounddevice()
        self._uninstall_recorder()
        self._uninstall_video()

    def _uninstall_video(self):
        self._uninstall_package('opencv-python')
        self._uninstall_package('opencv-python')

    def _uninstall_sounddevice(self):
        self._uninstall_package('sounddevice')
        self._uninstall_package('sounddevice')

    def _uninstall_recorder(self):
        self._uninstall_package('soundfile')
        self._uninstall_package('soundfile')

    def _uninstall_package(self, package):
        self._run_command(
            [
                _python_path,
                '-m',
                'pip',
                'uninstall',
                '-y',
                package
            ])

    def _install_all(self):
        if self._selected_target == 'addon-modules':
            libs_path_mkdir()
        self._ensure_pip()
        self._install_packages(["cffi", "sounddevice", "soundfile", "mido", "pygame"])
        # self._install_packages(["python-rtmidi"])
        self._install_packages(["opencv-python"], ["--no-deps"])

    def _install_packages(self, packages, add_params=None):
        if add_params is None:
            add_params = []
        install_target_params = []
        if self._selected_target == 'addon-modules':
            target_path = get_libs_path_latest()
            sys.path.append(target_path)
            install_target_params = ['--target', target_path]
        self._run_command(
            [
                _python_path,
                '-m',
                'pip',
                'install',
                # '--disable-pip-version-check',
                '--force-reinstall',
                '--upgrade',
            ] + install_target_params + add_params + packages)

    def _run_command(self, params):
        self.output_lines.append("\n")
        self.output_lines.append("RUN {}".format(" ".join(params)))
        self.output_lines.append("\n\n")
        start = time.time_ns()
        proc = subprocess.Popen(params,
                                stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

        read_out = _AsyncFileReader(proc.stdout)
        read_err = _AsyncFileReader(proc.stderr)
        read_out.start()
        read_err.start()

        while not read_out.eof() or not read_err.eof():
            while not read_out.queue.empty():
                time_diff = (time.time_ns() - start) / 1000000000
                line = read_out.queue.get()
                self.output_lines.append("info {:.1f}s: {}".format(time_diff, line))
            while not read_err.queue.empty():
                time_diff = (time.time_ns() - start) / 1000000000
                line = read_err.queue.get()
                self.output_lines.append("err {:.1f}s: {}".format(time_diff, line))
            time.sleep(.1)
