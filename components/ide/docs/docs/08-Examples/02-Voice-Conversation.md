# Offline Voice Conversation

This demonstration listens for a wake phrase, accepts several simple questions, and
plays prerecorded answers with CodyJoy Pro LED and buzzer feedback. It works offline.

## Prepare the answers

Connect a speaker. Open `generate_conversation_answers.py` from **CodyNick Examples**
and click **Run This File** once. It generates 27 WAV files in:

```text
/home/client/audio/conversation_answers
```

Running the generator again deliberately replaces the complete conversation-answer
set. Other recordings in `/home/client/audio` are not deleted.

## Start the conversation

Connect a USB microphone and speaker. Open `voice_conversation.py` and click
**Run This File**. Say `wake up` or `please wake up`. After the ready response, ask
several questions without repeating the wake phrase. The session remains awake until
ten seconds of silence.

Supported topics include greetings (`hello`, `hi`, `good morning`, `good afternoon`,
`good evening`, `good night`), identity, well-being, capabilities, favorite color,
feelings, and goodbye. Say `sleep` or `go to sleep` to return immediately to wake mode.

Each topic has three answers. The script selects them randomly without immediately
repeating the previous answer. Microphone capture stops during buzzer and speaker
output so the device does not recognize its own sounds.

## Feedback states

- Dim blue: waiting for the wake phrase.
- Green flash and rising notes: wake phrase accepted.
- Cyan center: listening for a question.
- Yellow side: processing.
- Green pattern: answering.
- Orange flashes and descending notes: question not recognized.
- Purple and farewell melody: goodbye.

Press **Stop** in the IDE to end the demonstration and release the microphone, speaker,
speech worker, serial connection, and LEDs.
