from dataclasses import dataclass, field
from typing import List, ClassVar, Mapping
from types import MappingProxyType
from components import *

@dataclass
class SyntaxTranslator:

    SYMBOL_MAP: ClassVar[Mapping[str, str]] = MappingProxyType({
        "TRUE": "true",
        "FALSE": "false",
        "≠": "!=",
        "¬": "!",
        "∧": "&&",
        "∨": "||",
        "≤": "<=",
        "≥": ">=",
        "=": "=="
    })

    def convert_expr(self, expr: str) -> str:
        expr = expr.strip()
        for k, v in self.SYMBOL_MAP.items():
            expr = expr.replace(k, v)
        return expr


@dataclass
class ContextTranslator:

    syntax: SyntaxTranslator = field(default_factory=SyntaxTranslator)

    def translate(self, contexts: List[EventBContext]) -> str:

        output: List[str] = []
        global_guards: List[str] = []

        for ctx in contexts:
            for a in ctx.axioms:
                raw = self.process_axioms(a)
                translation = self.syntax.convert_expr(raw)

                if translation:
                    if translation.startswith("enum "):
                        output.append(translation)
                    else:
                        global_guards.append(translation)

        if global_guards:
            guard_str = " && ".join(global_guards)
            output.append(f"#define GLOBAL_GUARD {guard_str};")
        else:
            output.append("#define GLOBAL_GUARD true;")

        return "\n".join(output)


    def process_axioms(self, axiom: EventBAxiom) -> str:
        # Maybe this process is best  to use AI APIs?
        result = axiom.predicate.strip()

        if result.startswith("partition("):
            result = result[len("partition("):-1]
            result = result.replace("{", "").replace("}", "")
            terms = [term.strip() for term in result.split(",")]
            if not terms:
                return ""
            return f"enum {terms[0]} {{{', '.join(terms[1:])}}};"
        return result