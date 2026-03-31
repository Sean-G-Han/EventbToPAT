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

class PatGenerator:

    def __init__(self, translator: SyntaxTranslator):
        self.translator = translator

    def generate(self, contexts: List[EventBContext], machines: List[EventBMachine]) -> str:
        parts = []
        parts.append(self._generate_contexts(contexts))
        parts.append(self._generate_machines(machines))
        return "\n".join(p for p in parts if p.strip())

    def _generate_contexts(self, contexts: List[EventBContext]) -> str:
        lines = []
        for ctx in contexts:
            for axiom in ctx.axioms:
                translated = self.translator.translate(
                    axiom.predicate,
                    context=TranslationContext.CONTEXT
                )
                lines.append(translated)
        return "\n".join(lines)

    def _generate_machines(self,machines: List[EventBMachine]) -> str:
        return "\n".join(
            self._generate_machine(machine)
            for machine in machines
        )


    def _generate_machine(self, machine: EventBMachine) -> str:
        parts = []
        parts.append(self._generate_initialisation(machine))
        parts.append(self._generate_process(machine))
        parts.append(self._generate_invariants(machine))
        return "\n".join(p for p in parts if p.strip())

    def _generate_initialisation(self, machine: EventBMachine) -> str:
        lines = []
        for event in machine.events:
            if event.is_initialisation():
                for action in event.then:
                    translated = self.translator.translate(
                        action.assignment,
                        context=TranslationContext.MACHINE_VAR
                    )
                    lines.append(translated)

        return "\n".join(lines)

    def _generate_process(self, machine: EventBMachine) -> str:
        event_clauses = []
        for event in machine.events:
            if event.is_initialisation():
                continue
            guards = [
                self.translator.translate(
                    g.predicate,
                    context=TranslationContext.MACHINE_CONDITION
                )
                for g in event.where
            ]

            actions = [
                self.translator.translate(
                    a.assignment,
                    context=TranslationContext.MACHINE_ACTION_THEN
                )
                for a in event.then
            ]

            guard_str = " && ".join(guards) if guards else "true"
            action_str = " ".join(actions)

            clause = f"[{guard_str}] {event.name}{{ {action_str} }} -> P"
            event_clauses.append(clause)

        if not event_clauses:
            return ""

        process_body = "\n[]\n".join(event_clauses)

        return f"P =\n{process_body};"

    def _generate_invariants(self, machine: EventBMachine) -> str:
        lines = []
        for invariant in machine.invariants:
            invariant_name = invariant.name
            if invariant_name == "":
                invariant_name = f"INV{PatGlobal.increment_assert_count()}"

            translated = self.translator.translate(
                invariant.predicate,
                context=TranslationContext.MACHINE_CONDITION
            )

            lines.append(f"#define {invariant_name} {translated};")
            lines.append(f"#assert P() |= []{invariant_name};")
        return "\n".join(lines)

if __name__ == "__main__":
    input_file = "context\\2_CAR.txt"
    output_file = "output.txt"
    parser = EventBParser(input_file)
    translator = SyntaxTranslator()
    generator = PatGenerator(translator)
    contexts, machines = parser.parse_file()
    pat_code = generator.generate(contexts, machines)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("// Generated PAT model from Event-B\n")
        f.write(f"enum {{{",".join(list(PatGlobal.enums))}}};\n")
        for index, term_name in enumerate(PatGlobal.enums):
            f.write(f"#define {term_name}_BIT {1 << index};\n")
        f.write(pat_code)
    print(f"Generated PAT model written to {output_file}")
    PatGlobal.print_globals()

    