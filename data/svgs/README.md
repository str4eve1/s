libratbag gnome theme
====================

Requirements
------------

See the Logitech G403 for an example of a device with a small amount of buttons,
and the Logitech G700 for an example of a device with a large amount of buttons.

- Canvas size should be between 400x400 and 500x500 pixels.
- Three layers in the final SVG:
  1. a lower layer named "Device" with the device itself. Each button on the
  device should have an id `buttonX`, with `X` being the number of the button
  (so for button 0 the id would be `button0`). Similarly, each LED on the device
  should have an id `ledX`.
  2. a middle layer named "Buttons" with the button leaders (see below for
  leaders).
  3. an upper layer named "LEDs" with the LED leaders.
- A leader line is a path that extends from the button or LED to the left or the
  right of the device (see below). Each leader line requires the following:
  - It should start with a 7x7 square placed on or close to the button or LED
    that it maps with.
  - From this square, a path should extend left or right (see below).
  - Each path should end with a 1x1 pixel with identifier `buttonX-leader` (or
    `ledX-leader`), where `X` is the number of the button (or LED) with
    which the leader maps. For button 0, this would be `button0-leader`.
  - All these elements should be grouped and given the identifier `buttonX-path`
    (or `ledX-path` for LEDs)
- Leader lines should have a vertical spacing of at least 40 pixels. When there
  are several leader lines above and below each other, make the spacing between
  them equal.
- If the device's scroll wheel supports horizontal tilting, add two small arrows
  left and right of the scroll wheel with the respective button identifiers (see
  the Logitech G700 for an example). Do not cut the scroll wheel in half
  vertically to map these buttons.
- If there aren't too many buttons, preferably make the leaders point to the
  right with the device itself placed on the left. If the buttons would extend
  below or above the device, make some point to the left instead with the device
  itself centered in the middle. In this case, half of the leaders should extend
  to the left and the other half to the right.
- When a leader points to the right, its 1x1 pixel should have a style property
  `text-align:start`. When a leader points to the left, its 1x1 pixel should
  have a style property `text-align:end`.
- The canvas should be resized so that there is a 20px gap between the device
  and the edge of the canvas and no gap between the 1x1 pixels and the canvas.

Please note that due to the way the SVG is drawn, you cannot rely on the
z-ordering of elements to line up or cover elements (as noted in [this
issue](https://github.com/libratbag/piper/issues/48), which includes links to
examples). As such, please make sure that you align the elements appropriately;
[this
comment](https://github.com/libratbag/piper/issues/48#issuecomment-315979109)
includes some helpful tips.

Technique
---------

The simplest approach is to find a photo of the device and import it into
inkscape. Put it on the lowest layer, create a new layer "Device" above it
and start tracing the outlines and edges of the device. Fill in the shapes
and your device should resemble the underlying photo. Delete the photo
layer, add leaders in their respective layers and you're done.

Make sure the image looks ''toned-down'' and not realistic. Do not use dark or
bright colors.


License
-------
The SVG files listed below were imported from libratbag and are MIT licensed
as of the time of import. See the libratbag COPYING file for details. The files
can also be licensed under pipers license (GPLv2).

 fallback.svg
 logitech-g-pro-wireless.svg
 logitech-g-pro.svg
 logitech-g102-g203.svg
 logitech-g300.svg
 logitech-g303.svg
 logitech-g402.svg
 logitech-g403.svg
 logitech-g500.svg
 logitech-g500s.svg
 logitech-g502.svg
 logitech-g600.svg
 logitech-g603.svg
 logitech-g604.svg
 logitech-g700.svg
 logitech-g703.svg
 logitech-g9.svg
 logitech-g900.svg
 logitech-mx-anywhere2.svg
 logitech-mx-anywhere2s.svg
 logitech-mx-master-2s.svg
 logitech-mx-master.svg
 roccat-kone-xtd.svg
 steelseries-kinzu-v2.svg
 steelseries-rival.svg
 steelseries-rival310.svg
 steelseries-rival600.svg
 steelseries-sensei310.svg
 steelseries-senseiraw.svg

Where changes are made to these files, the changes will be made under
piper's license (GPLv2). Use the git commit log to determine the exact
license state of each file.
