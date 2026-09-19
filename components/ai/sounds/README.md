# CodyNick camera sounds

Place the approved shutter asset here as `shutter_loud.wav`.

At runtime, `take_picture(..., get_ready_sound=True)` plays the CodyJoy Pro
countdown/capture notes and then this WAV through
`plughw:CARD=Audio,DEV=0`. The environment variables
`CODYNICK_SHUTTER_SOUND` and `CODYNICK_AUDIO_OUTPUT` can override those
defaults for an advanced installation.

If the WAV is absent, the controller uses the legacy buzzer shutter pattern.
