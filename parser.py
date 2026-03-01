import json
from EventbToPAT.components import *
from typing import List, Dict, Any, Tuple

# -----------------------------
# Parser Class
# -----------------------------

class EventBParser:
    """
    Parser for Event-B text files containing multiple JSON objects.
    """

    def __init__(self, filename: str) -> None:
        self.filename: str = filename
        self.contexts: List[EventBContext] = []
        self.machines: List[EventBMachine] = []

    def parse_file(self) -> None:
        """
        Parses the file and populates self.contexts and self.machines.
        """
        objects = self._read_json_objects(self.filename)
        for obj in objects:
            if "CONTEXT" in obj:
                self.contexts.append(EventBContext(obj))
            elif "MACHINE" in obj:
                self.machines.append(EventBMachine(obj))

    @staticmethod
    def _read_json_objects(filename: str) -> List[Dict[str, Any]]:
        """
        Read multiple JSON objects from a file.
        """
        objects: List[Dict[str, Any]] = []
        buffer: str = ""
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                buffer += stripped
                if stripped.endswith('}'):
                    try:
                        obj = json.loads(buffer)
                        objects.append(obj)
                        buffer = ""
                    except json.JSONDecodeError:
                        buffer += " "
        return objects

# -----------------------------
# Example Usage
# -----------------------------

if __name__ == "__main__":
    filename = "eventb_text.txt"  # Replace with your file path
    parser = EventBParser(filename)
    parser.parse_file()

    print(f"Loaded {len(parser.contexts)} contexts and {len(parser.machines)} machines.\n")

    for ctx in parser.contexts:
        print(f"Context: {ctx.name}, Sets: {ctx.sets}, Constants: {ctx.constants}, Axioms: {len(ctx.axioms)}")
        print(ctx)

    for mach in parser.machines:
        print(f"Machine: {mach.name}, Variables: {len(mach.variables)}, Invariants: {len(mach.invariants)}, Events: {len(mach.events)}")
        print(mach)
        for ev in mach.events:
            print(f"  Event: {ev.name}, Guards: {len(ev.where)}, Actions: {len(ev.then)}")
            print(ev)
            