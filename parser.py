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

            translated = self.translator.try_translate(
                invariant.predicate,
                context=TranslationContext.MACHINE_CONDITION
            )

            lines.append(f"#define {invariant_name} {translated};")
            lines.append(f"#assert P() |= []{invariant_name};")
        return "\n".join(lines)

if __name__ == "__main__":
    input_file = "context\\4_FILE_1.txt"
    output_file = "output.txt"
    parser = EventBParser(input_file)
    translator = SyntaxTranslator()
    generator = PatGenerator(translator)
    contexts, machines = parser.parse_file()
    pat_code = generator.generate(contexts, machines)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("// Generated PAT model from Event-B\n")
        if len(PatGlobal.functions) > 0:
            f.write("#import \"PAT.Lib.Custom_Programs\";\n")
        if len(PatGlobal.enums) > 0:
            f.write(f"enum {{{",".join(list(PatGlobal.enums))}}};\n")
        for index, term_name in enumerate(PatGlobal.enums):
            f.write(f"#define {term_name}_BIT {1 << index};\n")
        f.write(pat_code)
        f.write("\n// End of generated PAT model\n")
        if len(PatGlobal.functions) > 0:
            f.write(
                "/*AI Prompt for custom functions\n"
                "For the following functions, please provide write the function in C# as a library import for PAT. "
                "If unspecified you can assume all parameters and return type are integers.\n"
                "Preserve the parameters and behaviour. "
                "In the event that the function seem ambiguous you can assume anything "
                "as long as the math syntax is correct. For example...\n"
                "using System;\n"
                "using System.Collections.Generic;\n"
                "using System.Text;\n"
                "\n"
                "//the namespace must be PAT.Lib, the class and method names can be arbitrary\n"
                "namespace PAT.Lib\n"
                "{\n"
                "    /// <summary>\n"
                "    /// You can use static library in PAT model.\n"
                "    /// All methods should be declared as public static.\n"
                "    /// \n"
                "    /// The parameters must be of type \"int\", \"bool\", \"int[]\" or user defined data type\n"
                "    /// The number of parameters can be 0 or many\n"
                "    /// \n"
                "    /// The return type can be void, bool, int, int[] or user defined data type\n"
                "    /// \n"
                "    /// The method name will be used directly in your model.\n"
                "    /// e.g. call(max, 10, 2), call(dominate, 3, 2), call(amax, [1,3,5]),\n"
                "    /// \n"
                "    /// Note: method names are case sensetive\n"
                "    /// </summary>\n"
                "    public class Example\n"
                "    {\n"
                "        //==========================================================\n"
                "        //the following sections are the functions used by Mailbox \n"
                "        //==========================================================\n"
                "        private static List<int[]> Matrix;\n"
                "\n"
                "        //dominate(v,w) == CHOOSE x \in 1..7 : GT(x, v) /\ GT(x, w)\n"
                "        public static int dominate(int v, int w)\n"
                "        {\n"
                "            for (int i = 1; i <= 7; i++)\n"
                "            {\n"
                "                if (matrix[i - 1][v - 1] == 1 && matrix[i - 1][w - 1] == 1)\n"
                "                {\n"
                "                    return i;\n"
                "                }\n"
                "            }\n"
                "            return -1;\n"
                "        }\n"
                "    }\n"
                "}\n"
            )
            f.write(f"{PatGlobal.functions_to_string()}\n")
            f.write(f"*/\n")
    print(f"Generated PAT model written to {output_file}")
    PatGlobal.print_globals()

    