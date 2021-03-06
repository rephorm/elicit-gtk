Elicit
======

Elicit is a designers tool that allows one to magnify sections of the screen and select colors from any application, and organize those colors into palettes.

Here is what it looks like:

![Elicit Screenshot](https://github.com/rephorm/elicit-gtk/raw/master/data/screenshot.png)

Dependencies
============

Elicit is written in python for the gtk toolkit. As such, it requires:

* python 2.6+
* pygtk  2.16+
* pygobject 2.18+
* numpy 1.3+

Earlier versions may work, but have not been tested.

Installation
============

    # ./setup.py install
    $ elicit

If you want to run without installing, from the source directory run:

    $ PYTHONPATH=. ./bin/elicit

Additionally, there is now a dbus based remote control. Running

    $ elicit_remote magnify

OR

    $ elicit_remote select_color

will start magnification OR color selection. This can be connected to global key bindings if desired.

Usage
=====

Magnification
-------------
After running elicit, there is a large empty box at the top called the magnifier. Click on the magnifying class icon beneath this to begin zooming in on the portion of the screen under the mouse. Left click when the region you want is shown in the magnifier. The coordinates and size of the current selected region of the screen is shown beneath the magnifier on the left.

The size of the region of screen magnified is determined by the size of the magnifier. To obtain larger regions, increase the size of the window and then magnify again.

Scroll the mouse wheel over the magnifier to change the zoom level. After zooming in on the image, middle click and drag to pan around on the image.

By right clicking and dragging on the magnified image you can select a region of the image. The size and diagonal length of the selection are displayed beneath the magnifier.

Right click and release to remove the measurement box.

Use the left mouse button to drag the zoomed image to another application that can handle image data (e.g. the GIMP).

Check the 'Show Grid' checkbox to display the pixel grid over the magnified image.


Selecting Colors
----------------
Click on the eye dropper icon to begin color selection. The current color under the mouse is shown in the large swatch on the middle left.

The Red, Green and Blue values are shown to the right of the color picker, along with the Hue, Saturation and Value and hexidecimal RGB format.

Left click on the color picker to add the current color to the palette. You can also drag and drop the color from the swatch onto another application. If the application does not understand colors, but accepts text drops, a hex representation of the color will be dropped.

Palettes
--------

Below the color swatch is a section for managing palettes.

A dropdown list shows all available palettes. Typing in the textbox changes the name of the current palette.

To the right of the dropdown are two buttons for adding new palettes, or deleting ones you no longer wish to use.

Below this is the palette itself. Clicking on a color selects it, updating the color swatch and the color values above.

Colors can be rearranged by dragging them with the left mouse button. They can also be dragged to other applications. If you drop on a target that only understands text, the hex string will be copied.

If the palette contains more colors than fit on the screen, use the scroll wheel or middle-drag to pan.

Right click on a color to remove it from the palette.

Finally, you can edit the name of the selected color by changing it in the 'Color Name' textbox.

The palettes are stored in the GIMP palette formate (.gpl) in the 'palettes' subdirectory of the user's configuration directory (usually ~/.config/elicit/)

Remote
------

Elicit can also be controlled via a remote control application named `elicit_remote`. This can be used to implement desktop wide keyboard shortcuts. For example, one could bind the `Search` key (`XF86Search`) to run `elicit_remote magnify`. If elicit is not currently running, it should launch and then begin magnifying. If it is already running, it will simply start magnifying. To begin selecting a color, run `elicit_remote select_color`.

Alternatively, one can use DBus to connect to the `/com/rephorm/Elicit` object on the `com.rephorm.elicit` bus. The interface `com.rephorm.Elicit` implements two methods: `Magnify()` and `SelectColor()`. These methods take no parameters and return void.

Vim Support
-----------

Elicit includes integration with the Vim text editor. This allows one to easily pass color values between Vim and Elicit.

To install, I recommend using [pathogen][pathogen] to manage vim plugins. Then, just copy (or symlink) Elicit's vim/ directory into your .vim/bundle/ directory.

For more information, see vim/doc/elicit.vim

I have also made a [screencast demonstrating the vim plugin][screencast].

[screencast]: http://www.youtube.com/watch?v=1h5VB9hUg-E
[pathogen]: https://github.com/tpope/vim-pathogen
