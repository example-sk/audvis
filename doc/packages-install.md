# Installing Python Packages

If you want to use [Realtime Analyzer](./realtime.md), 
[MIDI File](./midi-file.md), [MIDI Realtime](./midi-realtime.md)
or [Video Capture](./video-capture.md), you need to install python
packages. Everything should be done only by clicking on button 
"Install python packages" under any of mentioned panels. After clicking
on this button, a new window opens with installation log. If everything
works fine, you should see something like this:

```
"""
RUN /opt/blender/3.1/3.1/python/bin/python3.9 -m ensurepip --altinstall --user

info 2.8s: Looking in links: /tmp/tmpikxtby4l
info 2.8s: Requirement already satisfied: setuptools in ./.local/lib/python3.9/site-packages (49.2.1)
info 2.8s: Processing /tmp/tmpikxtby4l/pip-21.2.3-py3-none-any.whl
info 2.9s: Installing collected packages: pip
info 4.3s: Successfully installed pip-21.2.3

... (more lines) ...

RUN /opt/blender/3.1/3.1/python/bin/python3.9 -m pip install --force-reinstall --upgrade --target /home/r/.config/blender/3.1/scripts/addons/modules/_audvis_modules/a_1639510547 --no-deps opencv-python

info 1.8s: Collecting opencv-python
info 1.9s:   Downloading opencv_python-4.5.4.60-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (60.3 MB)
info 8.4s: Installing collected packages: opencv-python
info 9.9s: Successfully installed opencv-python-4.5.4.60


FINISHED!


"""
```

## Troubleshooting:

If you see errors in the log, you can go to `Edit -> Preferences -> Add-ons -> AudVis`
and change the "Install directory" to "Blender" instead of default
"User Add-On Modules", and click on (Re)Install button.

### Windows:
- You may need to install [Microsoft Visual C++ 2015 Redistributable Update 3 RC.](https://www.microsoft.com/en-us/download/details.aspx?id=52685)
- Try running Blender as Administrator, and press install button again. ([how to run a program as administrator](https://www.youtube.com/watch?v=nNVdaJXYCbA))
- If you want to use Realtime Analyzer, setup Stereo Mix ([video instructions here](https://youtu.be/Bd3moKLV5sE))

### Linux:
- You may need to install libportaudio2 (on debian or ubuntu, the command is `sudo apt-get install libportaudio2`).

### MacOs:
- Mac computers come with different processor types. Only tested with MacBook Air mid 2012. It would be nice if you test this on other hardware and let me know if it worked.
- For Realtime Analyzer, you may need to install Soundflower or similar software ([video instructions here](https://www.youtube.com/results?search_query=soundflower+macos).
