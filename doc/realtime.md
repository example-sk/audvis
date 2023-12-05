# Realtime Analyzer

Read first: [Installing Python Packages](./packages-install.md)

Realtime Analyzer is the first part of AudVis and the reason, why this whole project has started.

AudVis reads data from your microphone or sound capture using Python package `sounddevice`. Most of the setup is usually
done outside of Blender and AudVis. You need to setup your operating system settings:
- on Linux, everything should work as expected
- on Windows, setup [Stereo Mix](https://www.google.com/search?q=windows+stereo+mix)
- on MacOS, you need a 3rd party software like [Soundflower](https://www.google.com/search?q=soundflower) or [Blackhole](https://www.google.com/search?q=macos+blackhole)

Sometimes it can frustrating and sometimes, in case of some exotic hardware combinations, it can be almost impossible to make
everything work. You have been warned.

If everything works, [Fast Fourier Transform](https://en.wikipedia.org/wiki/Fast_Fourier_transform) is performed for
every frame of Blender scene. This means you need to play animation to watch any animation. The result of FFT is stored
and then used when needed, for example by [drivers](./drivers.md), [Shape modifier](./shape-modifier.md)
or [Spectrogram](./spectrogram.md).

## Settings:

- **Enable** (in the Realtime Analyzer panel header): do you want to use Real Time Analyzer? If not, keep this disabled
- **Input Device**: choose the device you want to "listen"
- **Auto Switch Scenes**: if you have multiple scenes, they will alternate. Please, don't use scenes with too small
  number of frames