import os
import subprocess
import sys
import threading
from glob import glob


class PipinstallerThread(threading.Thread):
    packages = []
    status = 'init'

    # PipinstallerThread
    def add(self, packages, deps=True):
        if type(packages) == str:
            packages = [packages]
        self.packages.append([packages, deps])
        return self

    def run(self):
        self.status = 'trying ensurepip'
        python_path = _get_python_path()
        subprocess.call([python_path, '-m', 'ensurepip', '--altinstall'])
        for item in self.packages:
            packages = item[0]
            deps = item[1]
            self.status = 'trying ' + ' '.join(packages)
            deps_args = []
            if not deps:
                deps_args = ['--no-deps']
            output = subprocess.check_output(
                [python_path, '-m', 'pip', 'install', '--force-reinstall'] + deps_args + packages,
                universal_newlines=True
            )
        self.status = 'success'


def _get_python_path():
    f = glob(os.path.join(os.path.realpath(sys.prefix), 'bin', 'python*'))
    return f[0]
