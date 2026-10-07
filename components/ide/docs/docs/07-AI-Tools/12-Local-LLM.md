# Local Language Model

CodyNick includes an offline Gemma 3 1B Instruct language model. It runs locally
on the Raspberry Pi and does not send questions to an internet service.

## Basic use

```python
from codynick_ai import CodyNickAI

ai = CodyNickAI()

print("Preparing local AI...")
ai.load_llm()
print("AI is ready.")

answer = ai.ask("Why do plants need sunlight?")
print(answer)

ai.close()
```

`load_llm()` loads the model explicitly. Loading takes several seconds, but the
model remains available for every later `ask()` call in the same program.

## IDE question example

```python
from codynick_ai import CodyNickAI

question = "Explain an RGB LED in one short sentence."
ai = CodyNickAI()
try:
    ai.load_llm()
    print(ai.ask(question))
finally:
    ai.close()
```

The IDE does not provide terminal input to background student scripts. Edit the
`question` value and run the file again, or use the bundled voice conversation.

## API reference

### `load_llm(context_size=2048, threads=4)`

Loads Gemma and waits until it can accept questions. Calling it again in the same
process returns immediately. `context_size` may be 256 through 4096; a larger value
uses more memory. `threads` may be 1 through 8.

### `ask(question, system_prompt=..., max_tokens=40, temperature=0.2)`

Returns the generated answer as a string. Call `load_llm()` first. The default
system prompt requests one brief sentence and asks the model not to invent facts.
Use a low temperature for predictable answers.

```python
answer = ai.ask(
    "What is an RGB LED?",
    max_tokens=30,
    temperature=0.1,
)
```

### `unload_llm()`

Stops the local model and releases its memory. Call `load_llm()` again before the
next question.

### `close()`

Releases the LLM, camera, and any other CodyNick AI worker owned by the program.
The library also registers process-exit cleanup, but explicit cleanup is clearer.

## Limits

The model occupies approximately 1.35 GB while loaded. Avoid loading multiple
copies or combining it with several other large AI models on a 4 GB Pi. Answers
come from the model's training and can be incorrect. This release does not include
RAG or internet search.

## Local AI voice conversation

`local_ai_voice_conversation.py` loads separate STT and TTS workers plus Gemma before
conversation begins. Say `wake up`, ask unrestricted short questions, say `sleep` to
return to wake mode, or say `stop listening` to exit. It constrains answers to fewer
than ten words, pauses microphone capture during speech, reuses `llm_answer.wav`, and
uses CodyJoy Pro LEDs and notes for each interaction state. Conversation history is
not retained between questions.
