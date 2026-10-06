"""Ask the offline Gemma assistant several short questions."""
from codynick_ai import CodyNickAI


ai = CodyNickAI()

print("Preparing local AI...")
ai.load_llm()
print("AI is ready. Type exit to finish.")

while True:
    question = input("You: ").strip()

    if question.lower() == "exit":
        break

    if question:
        print("AI:", ai.ask(question))

ai.close()
