# Video Capture

Use only with Realtime Analyzer. Reads images from your webcam with opencv and updates the **Output Image**.

**Warning!** Because some api issues, audvis first saves the captured image to your HDD or SSD and then loads it into
Blender. This brings performance issues and also this
can [wear out your SSD](https://www.dell.com/support/kbdoc/en-us/000137999/hard-drive-why-do-solid-state-devices-ssd-wear-out?lang=en)
. If you are running Blender on Linux, you can
setup [tmpfs](https://www.kernel.org/doc/html/latest/filesystems/tmpfs.html) and set the **Temp Path** property to a
directory inside tmpfs partition. On Windows, search for ImDisk or RamDisk. You don't need a lot of space. 100MB is more
than enough. It looks MacOs doesn't have

If you are using MacOs, you need to run Blender manually from Terminal to ask for permissions. Open Terminal and
run `/Applications/Blender.app/Contents/MacOS/blender`

## Settings

- **Camera Index** - if you have multiple cameras, choose which one you want to use
- **Temp Path** - where to periodically save temporary image. If empty, temporary directory is created internally