import json
from typing import List, Dict, Any, Tuple
from components import *
from syntaxTranslator import *
import argparse
import re
import argparse
import re

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
            for const in ctx.constants:
                PatGlobal.add_constant(const)
            for set_name in ctx.sets:
                PatGlobal.add_set(set_name)
            for axiom in ctx.axioms:
                translated = self.translator.try_translate(
                    axiom.predicate,
                    context=TranslationContext.CONTEXT
                )
                lines.append(translated) if len(translated) > 0 else None
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
            for any in event.any:
                PatGlobal.add_variable(any)
            if event.is_initialisation():
                for action in event.then:
                    translated = self.translator.try_translate(
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
                self.translator.try_translate(
                    g.predicate,
                    context=TranslationContext.MACHINE_CONDITION
                )
                for g in event.where
            ]

            actions = [
                self.translator.try_translate(
                    a.assignment,
                    context=TranslationContext.MACHINE_ACTION_THEN
                )
                for a in event.then
            ]

            guard_str = " && ".join(guards) if guards else "true"
            action_str = " ".join(actions)

            clause = f"[{guard_str}] {event.name}{{ {action_str} }} -> Process"
            clause = f"[{guard_str}] {event.name}{{ {action_str} }} -> Process"
            event_clauses.append(clause)

        if not event_clauses:
            return ""

        process_body = "\n[]\n".join(event_clauses)

        return f"Process =\n{process_body};"
        return f"Process =\n{process_body};"

    def _generate_invariants(self, machine: EventBMachine) -> str:
        lines = []
        for invariant in machine.invariants:
            invariant_name = invariant.name
            if invariant_name == "":
                invariant_name = f"INV{PatGlobal.increment_assert_count()}"

            translated = self.translator.try_translate(
                invariant.predicate,
                context=TranslationContext.MACHINE_CONDITION
            )

            lines.append(f"#define {invariant_name} {translated};")
            lines.append(f"#assert Process() |= []{invariant_name};")
            lines.append(f"#assert Process() |= []{invariant_name};")
        return "\n".join(lines)

def main(filename: str, output: str = "output.txt") -> bool:
    input_file = f"context\\{filename}.txt"
    output_file = output

    parser_obj = EventBParser(input_file)
    translator = SyntaxTranslator()
    generator = PatGenerator(translator)

    contexts, machines = parser_obj.parse_file()
    pat_code = generator.generate(contexts, machines)

    declared_vars = set(re.findall(r"\bvar\s+([a-zA-Z_][a-zA-Z0-9_]*)\b", pat_code))
    undeclared_vars = PatGlobal.variables - PatGlobal.enums - declared_vars

    auto_declare_section = "\n// Auto-declared variables (used but not declared)\n"
    for var_name in sorted(undeclared_vars):
        auto_declare_section += f"var {var_name} = 0;\n"
    auto_declare_section += "\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("// Generated PAT model from Event-B\n")

        if len(PatGlobal.functions) > 0:
            f.write("#import \"PAT.Lib.Custom_Programs\";\n")

        if len(PatGlobal.enums) > 0:
            f.write(f"enum {{{','.join(list(PatGlobal.enums))}}};\n")
            for index, term_name in enumerate(PatGlobal.enums):
                f.write(f"#define {term_name}_BIT {1 << index};\n")

        f.write(auto_declare_section)

        f.write(pat_code)
        f.write("\n// End of generated PAT model\n")

        # Restore AI section
        if PatGlobal.get_ai_used():
            with open("prompt.txt", "r", encoding="utf-8") as prompt:
                f.write("\n")
                f.write(prompt.read())
                f.write("\n")
                f.write(PatGlobal.functions_to_string())
                f.write(PatGlobal.functions_to_string())

            f.write("*/\n")
            return True
        return False

    print(f"Generated PAT model written to {output_file}")
    PatGlobal.print_globals()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Event-B to PAT Translator")
    parser.add_argument("filename")
    parser.add_argument("-o", "--output", default="output.txt")

    args = parser.parse_args()
    main(args.filename, args.output)