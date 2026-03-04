import json
from typing import List, Dict, Any, Tuple
from components import *
from syntaxTranslator import *

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
                line = line.replace("\\t", "")
                line = line.replace("\\n", "")
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
    filename = "context\\2_CAR.txt"
    parser = EventBParser(filename)
    syntax_translator = SyntaxTranslator()
    contexts, machines = parser.parse_file()

    print(f"Loaded {len(contexts)} contexts and {len(machines)} machines.\n")

    for ctx in contexts:
        for a in ctx.axioms:
            predicate = a.predicate
            print(syntax_translator.translate(predicate, purpose=TranslationPurpose.CONTEXT))
    
    for mach in machines:
        init = filter(lambda e: e.is_initialisation(), mach.events)
        events = filter(lambda e: not e.is_initialisation(), mach.events)
        for ev in init:
            for a in ev.then:
                assignment = a.assignment
                print(syntax_translator.translate(assignment, purpose=TranslationPurpose.MACHINE_VAR))
        event_clauses = []
        for ev in events:
            guards = []
            actions = []
            for g in ev.where:
                guard = g.predicate
                guards.append(syntax_translator.translate(guard, purpose=TranslationPurpose.MACHINE_CONDITION))
            for a in ev.then:
                assignment = a.assignment
                actions.append(syntax_translator.translate(assignment, purpose=TranslationPurpose.MACHINE_ACTION_THEN))
            guard_str = " && ".join(guards) if guards else "true"
            action_str = " ".join(actions)
            event_clause = f"[{guard_str}] {ev.name}{{ {action_str} }} -> P"
            event_clauses.append(event_clause)
        process_body = "\n[]\n".join(event_clauses)
        print(f"P =\n{process_body};\n")

    for mach in machines:
        for inv in mach.invariants:
            invariant = inv.predicate
            translation = syntax_translator.translate(invariant, purpose=TranslationPurpose.MACHINE_CONDITION)
            count = PatGlobal.increment_define_count()
            print(f"#define INVARIANT{count} {translation};")
            print(f"#assert P() |= []INVARIANT{count};")

    # for mach in machines:
    #     print(f"Machine: {mach.name}, Variables: {len(mach.variables)}, Invariants: {len(mach.invariants)}, Events: {len(mach.events)}")
    #     print(mach)
    #     for inv in mach.invariants:
    #         print(inv)
    #     for ev in mach.events:
    #         print(f"  Event: {ev.name}, Guards: {len(ev.where)}, Actions: {len(ev.then)}")
    #         print(ev)