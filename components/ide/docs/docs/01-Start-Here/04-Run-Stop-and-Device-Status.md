# Run, Stop, and Device Status

## IDE and Block Coding

Run saves the selected/generated Python and starts it. Run works again after Stop,
even if the program has not changed. Stop ends the active student program, including
its child processes, without stopping the watchdog, web tools, or simulator service.
Saving code or a workspace after Stop does not start the stopped program.

Allow up to 10 seconds for normal Python cleanup before systemd forces termination.
The IDE terminal remains visible. A stopped simulator script releases its stage lease
after a short delay, allowing gadgets to be added or removed. Real gadget LEDs may
remain lit unless the program clears them during cleanup.

Both tools control the same active program. Stopping in one stops a program launched
from the other. The control socket is restricted to root and the web-server account,
accepts only Start/Stop, and does not require sudo or weaker Apache security settings.

## Navigation and Favicon

Use the Main Panel button in each tool header. The CodyNick favicon identifies the
device pages. After an upgrade, use Ctrl+F5 and reopen a tab if an old favicon persists.

## CJP Firmware on the Main Panel

A successful physical connection records the firmware version and detection time in
UTC. Refresh the main panel to see the latest recorded information. No extra serial
connection is opened by the panel. Before detection it shows Not detected yet; older
firmware that does not report a version shows Unknown. Simulator connections do not
overwrite physical device status. Last detected does not imply currently connected.
