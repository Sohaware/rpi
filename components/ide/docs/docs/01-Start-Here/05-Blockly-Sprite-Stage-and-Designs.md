# Blockly Sprite Stage and Designs

## First Project

Open Block Coding from the main panel. The stage is integrated beside the workspace;
Stage shows/hides it. On small screens the stage appears below the blocks.

Download the [demo design](/blocks/examples/sprite_demo.codynick), then Upload it in
Blockly. Download your current project first if you want to keep it. Click Run, click
the stage to focus it, and hold the left/right arrows. Stop ends the active program.
Sprite-only projects do not open a CJP port; adding hardware blocks connects to CJP.

## Toolbox Tabs

- General: Events, Operators, Control, Text, Timer, Variables.
- Sprites: Motion (blue), Looks (magenta), Sensing (teal).
- Hardware: existing gadget categories.

Tabs change only the toolbox, never the program. Mix sprite and gadget blocks in
one workspace. Timer reports decimal seconds from program start or the last reset;
it uses a monotonic clock rather than calendar time.

## Sprite Blocks

The stage is 480 by 360 units. Its center is x=0,y=0, right is positive x, up is
positive y. Coordinates range from -240 to 240 and -180 to 180.

| Category | Commands and values |
| --- | --- |
| Motion | Move steps; turn clockwise; point in direction; go to x/y; set/change x/y; glide seconds to x/y; bounce at edge; go to mouse; x, y, direction values |
| Looks | Say; say for seconds; show/hide; set/change size; size value |
| Sensing | Key pressed; mouse x/y; mouse down; touching edge |

Direction is 0 up, 90 right, 180/-180 down, -90 left. Size is a percentage clamped
to 10..300; negative change-size values shrink the sprite. Bounce accounts for size
and rotation. Glide and timed speech take 0..300 seconds and pause the current
Python program until finished; Stop interrupts the program. Timed speech expires
on the stage even if the script has stopped. Keyboard input releases on focus loss,
and stale keyboard/mouse-down input expires if the browser disconnects.

Start x/y, direction, size and backdrop are saved with the design. These settings
apply on Run or Reset; runtime motion does not replace the saved starting settings.

## Save, Load, Delete and Transfer

Enter a Design Name and click Save. This stores blocks, variables and stage settings
on the device. Save confirms before overwriting an existing name. Load lists device
designs, confirms replacement of unsaved named work, and never starts execution.

Delete in Load removes only the selected saved copy after confirmation. It does not
clear the open workspace or stop a running program. Deletion cannot be undone.
The open copy can be saved again to recreate a deleted saved design.

Download uses `Design Name.codynick` (Untitled if blank); Upload selects `.codynick`.
Old exported designs can be renamed to `.codynick` without conversion. Device design
names are case-sensitive, at most 120 UTF-8 bytes, without slashes/control characters.
The device supports 500 named designs, up to 2 MB each.

The recovery autosave remains separate from explicit named Save. Named designs live
in `/var/www/html/blocks/data/designs/`; upgrades do not replace that directory.

## Limits and Rollback

One built-in sprite, three plain backdrops, one shared stage per device. Use one
focused browser tab for input. Costumes, uploads, multiple sprites, broadcasts,
parallel Scratch scripts, remote hosting and PC runtimes are not included.

The stage runs as client on 127.0.0.1:8092; Apache exposes only stage-state commands.
It does not execute Python or access USB hardware. Keep this coding device on a
trusted network, not the public internet. The normal student service runs Python.

Older releases cannot edit sprite/Timer projects. Download important projects before
downgrading. Named designs remain on disk and the active workspace is backed up
under `/var/backups/codynick/core-*/var/www/html/blocks/data/main.json`.
