"""Ask the offline Gemma assistant one editable question."""
from codynick_ai import CodyNickAI


question = "Explain an RGB LED in one short sentence."

ai = CodyNickAI()
try:
    print("Preparing local AI...", flush=True)
    status = ai.load_llm()
    seconds = status.get("loading_seconds")
    print(f"Local AI is ready{f' after {seconds} seconds' if seconds else ''}.", flush=True)
    print("Question:", question, flush=True)
    print("Answer:", ai.ask(question), flush=True)
finally:
    ai.close()
    print("Local AI stopped.", flush=True)
