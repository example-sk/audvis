# Sequence Analyzer

Sequence analyzer is similar to [Realtime Analyzer](./realtime.md), but uses sound sequences in Blender's Video Sequence
Editor. Don't worry if you don't like the VSE, there is a quite good user interface inside AudVis "Sequence Analyzer"
panel.

## Settings

- **Enable** (in the Sequence Analyzer panel header): do you want to use Sequence Analyzer? If not, keep this disabled
- **Enable** single sequence - you can enable/disable every single sound sequence for use in AudVis Sequence Analyzer
- **Add Sound Sequence** - choose a sound file to use. You can use multiple sound files, and animate different things by
  different sound files
- **Remove Sound Sequence** - remove selected sound sequence
- **Name** - name of the sequence. You can change it or copy the name to use it in the [driver](./drivers.md) expression
- **Start Frame** - this is important! This is the frame when the sound sequence starts to play and also AudVis starts
  to parse it
- **Start Offset** - just offset - you can cut out the start of the song for example
- **Length** - just length - you can cut out the end of the song for example
- **Align End Frame by Sequences** - set current scene's End Frame to the last frame of all sound sequences - if your
  song is 1234 frames long and starts at frame 1, end frame of the scene will be set to 1235
