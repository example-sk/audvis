# Spectrogram

A spectrogram is a visual representation of the spectrum of frequencies of a signal as it varies with
time ([Wiki](https://en.wikipedia.org/wiki/Spectrogram)). In Blender, it's really powerful tool. You can use it in
Geometry Nodes, in old school Textures, in shading nodes... I'm not even able to name a fraction of the potential uses.

## Settings

- **Multiple Freq properties** - the whole concept is [described here](./freq-sequencing.md)
- **Mode**
    - **Rolling** - for every frame, the whole image is moved 1 pixel up (upmost pixel is lost), and then current data
      will be drawn into the bottom 1px line
    - **One Image** - the height of the image will be the same as your scene's duration - if it's 1000 frames, the image
      will be 1000 pixels high. Every line of image represents one frame. The main advantage is that you have only 1
      image and you don't need to handle baked image sequences.
    - **Snapshot** - all pixels will be filled by current data
- **Image Width** - if the image's width isn't the same as this value, it will be resized
- **Image Height** (only if Rolling or Snapshot Mode is selected) - if the image's height isn't the same as this value,
  it will be resized. **Warning!** Snapshot mode with high width+height values will result in poor performance. 100x100
  pixels in snapshot mode means 10,000 calls for data, which is more than you want and need
- **Factor RGB** - multiply returned point value by these values. If you put 3 same values, the result image will be
  black and white. If not, it will be more colorful
- **Skip Frames** - if higher than 0, lower number of frames will be drawn. 1 means every second frame, 2 means every
  third frame will be drawn.
- **Clear on First Frame** - if **One Image** or **Rolling** mode is selected, the image will be cleared on the frame
  1 (or whatever frame is your Start Frame)
- **Base Color** - this will be background color and will be added to the animated values
- **Bake Path** - path to the directory where you want to bake spectrogram images
- **Bake Spectrogram** - perform the baking. In case of **One Image** mode, only one image will be saved. In other
  cases, images named "audvis-spect-0001.png", "audvis-spect-0002.png"... will be saved to selected **Bake Path** 