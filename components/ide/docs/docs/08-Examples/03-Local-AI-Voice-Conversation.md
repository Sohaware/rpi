# Local AI Voice Conversation

This demonstration combines offline speech recognition, Gemma, generated speech, and
CodyJoy Pro feedback. Connect CodyJoy Pro, a USB microphone, and a speaker. Open
`local_ai_voice_conversation.py` and choose **Run This File**.

## Test sequence

1. Wait for TTS, speech recognition, and Local AI to report ready.
2. Say `wake up` and wait for `I am listening`.
3. Ask one short question at a time.
4. Say `sleep` to return to wake mode, or remain quiet for ten seconds.
5. Say `stop listening` or `goodbye` to exit.

The dim blue LED means waiting, green with rising notes means awake, cyan center LEDs
mean listening, yellow side LEDs mean processing, and the green answer pattern means
the response is being spoken. Purple LEDs and descending notes indicate goodbye.

All three models load once before conversation begins. The microphone stops during
buzzer and speaker output, preventing self-recognition. Answers are limited to nine
words and stored repeatedly as `llm_answer.wav`; previous temporary answers are
replaced. The demonstration does not preserve conversational history.
