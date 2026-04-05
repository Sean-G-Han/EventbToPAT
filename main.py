import llm_translator
import parser

if __name__ == "__main__":
    print("Starting Event-B to PAT translation...")
    is_ai_used = parser.main("90_DOORS")

    if is_ai_used:
        print ("AI translation requested. Starting LLM translation...")
        translator = llm_translator.PATTranslator()
        translator.translate_file(
            "output.txt",
            "translated_output.txt"
        )
        print("LLM translation complete. Final output is in translated_output.txt")
    else:
        print("No AI translation needed. Output is ready in output.txt")