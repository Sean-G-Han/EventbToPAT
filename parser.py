import json
from typing import List, Dict, Any, Tuple
from components import *
from converter import *

class EventBParser:
    """
    Parser for Event-B text files containing multiple JSON objects.
    """

    def __init__(self, filename: str) -> None:
        self.filename: str = filename


    def parse_file(self) -> Tuple[List[EventBContext], List[EventBMachine]]:
        """
        Parses the file and returns contexts and machines.
        """
        contexts: List[EventBContext] = []
        machines: List[EventBMachine] = []

        objects = self._read_json_objects()

        for obj in objects:
            if "CONTEXT" in obj:
                contexts.append(EventBContext.from_dict(obj))
            elif "MACHINE" in obj:
                machines.append(EventBMachine.from_dict(obj))

        return contexts, machines


    def _read_json_objects(self) -> List[Dict[str, Any]]:
        """
        Reads multiple JSON objects from the file.
        """

        objects: List[Dict[str, Any]] = []
        buffer: str = ""

        with open(self.filename, "r", encoding="utf-8") as f:

            for line in f:
                stripped = line.strip()

                if not stripped:
                    continue

                buffer += stripped
                if stripped.endswith("}"):
                    try:
                        obj = json.loads(buffer)
                        objects.append(obj)
                        buffer = ""
                    except json.JSONDecodeError:
                        buffer += " "

        return objects

if __name__ == "__main__":
    filename = "eventb_text.txt"  # Replace with your file path
    parser = EventBParser(filename)
    contexts, machines = parser.parse_file()

    print(f"Loaded {len(contexts)} contexts and {len(machines)} machines.\n")

    # for ctx in contexts:
    #     print(ctx)

    # for mach in machines:
    #     print(f"Machine: {mach.name}, Variables: {len(mach.variables)}, Invariants: {len(mach.invariants)}, Events: {len(mach.events)}")
    #     print(mach)
    #     for ev in mach.events:
    #         print(f"  Event: {ev.name}, Guards: {len(ev.where)}, Actions: {len(ev.then)}")
    #         print(ev)

    ctx_trans = ContextTranslator() # enums and defines
    print(ctx_trans.translate(contexts))