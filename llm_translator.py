from openai import OpenAI

OPENAI_API_KEY = "[YOUR_OPENAI_API_KEY]"

class PATTranslator:

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def translate_file(self, input_file, output_file):
        print("  Reading output.txt...")
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
        print("Sending full file to LLM...")
        response = self.client.responses.create(
            model="gpt-5.4",
            input=content
        )
        translated = response.output_text
        print("  Writing translated file...")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(translated)
        print("  Translation complete.")


def main():
    translator = PATTranslator()
    translator.translate_file(
        "output.txt",
        "translated_output.txt"
    )

if __name__ == "__main__":
    main()