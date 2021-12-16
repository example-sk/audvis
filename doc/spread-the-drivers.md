# Spread the Drivers

If you right click on an animatable property, you should see an option on the last position in the
menu: `Audvis: Spread the Drivers`. There is also a panel named "Spread the Drivers" where you can see what is happening
and where you can tweak things.

# Settings

- **Multiple Freq properties** - the whole concept is [described here](./freq-sequencing.md)
- **Expression** - you can write your own expression and string "audvis()" will be replaced by the generated expression.
  If you put there `clamp(audvis() * 2.5, 0, 10)`, the result expression will be something like `clamp(audvis(50, 100) * 2.5, 0, 10)`