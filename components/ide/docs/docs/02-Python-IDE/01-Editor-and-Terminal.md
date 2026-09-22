# Python IDE and Live Terminal

The IDE edits `/home/client/active_script.py`. **Run This File** saves the editor,
then the CodyNick watchdog restarts the student-script service when the file changes.

The editor and terminal have independent scroll areas. The surrounding page should
remain fixed. Terminal colors are rendered in the browser, so Python output containing
ANSI color codes should not display raw escape characters.

## Typical workflow

1. Choose or edit a file.
2. Select **Run This File**.
3. Read startup messages and errors in the live terminal.
4. Correct the code and run it again.

The **Images** and **Audio** areas expose files created by camera, OCR, and speech
examples. Reusing stable names keeps these folders tidy.

## Stopping resources

Bundled examples close serial devices, microphones, AI workers, and cameras in
`finally` blocks. A one-shot camera capture also releases the webcam immediately.
Programs that intentionally keep a camera open must call `ai.close_camera()` when the
capture loop ends and `ai.close()` before exit.

