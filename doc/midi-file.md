# MIDI File

If you want to animate things by MIDI File, this is what you are searching for. AudVis will read the file using Python
module mido, and save the parsed data into animation data.

## Settings

- **Enable** (in the Midi File panel header): do you want to use Midi File feature? If not, keep this disabled
- **Enable** single midi file - you can enable/disable every single midi file for use in AudVis
- **Add Midi File** - choose a midi file to use. You can use multiple midi files, and animate different things by
  different midi files
- **Remove Midi File** - remove selected midi file
- **Name** - internal name of the midi file. You can change it or copy the name to use it in the [driver](./drivers.md)
  expression
- **Frame Start** - frame when to start using this midi file
- **Hold Offset Start** - just offset - you can cut out the start of the song for example
- **Hold Offset End** - just offset - you can cut out the end of the song for example
- **Tracks** - list of tracks inside selected file
- **Track Name** - You can change it or copy the name to use it in the [driver](./drivers.md) expression
- **Remove Midi Track** - you can remove single track from a midi file (this doesn't affect the MIDI file on the disk) 