from dataclasses import dataclass
from typing import List, Dict, Any
from components import *


@dataclass
class SyntaxTranslator:

    SYMBOL_MAP = {
        "TRUE": "true",
        "FALSE": "false",
        "≠": "!=",
        "¬": "!",
        "∧": "&&",
        "∨": "||",
        "≤": "<=",
        "≥": ">=",
        "=": "=="
    }

    @staticmethod
    def convert_expr(expr: str) -> str:

        expr = expr.strip()

        # Doesnt cover stuff like ∈ which likely need fancy logic
        for k in SyntaxTranslator.SYMBOL_MAP.keys():
            expr = expr.replace(k, SyntaxTranslator.SYMBOL_MAP[k])
        
        return expr


@dataclass
class ContextTranslator:

    @staticmethod
    def translate(contexts: List[EventBContext]) -> str:
        output: List[str] = []

        global_guards: List[str] = []

        for ctx in contexts:
            for a in ctx.axioms:
                translation = ContextTranslator.process_axioms(a)
                if translation:
                    if translation.startswith("enum "): # potential edgecasee... if a condition calls itself enum
                        output.append(translation)
                    else:
                        global_guards.append(translation)

        if global_guards:
            guard_str = " && ".join(global_guards)
            output.append(f"#define GLOBAL_GUARD {guard_str}")
        else:
            output.append("#define GLOBAL_GUARD true")

        return "\n".join(output)

    @staticmethod
    def process_axioms(axiom: EventBAxiom) -> str:
        result = axiom.predicate.strip()

        # enums
        if result.startswith("partition("):
            result = result[len("partition("):-1]
            result = result.replace("{", "")
            result = result.replace("}", "")
            terms = [term.strip() for term in result.split(",")]
            if not terms:
                return ""
            return f"enum {terms[0]} {{{', '.join(terms[1:])}}}"
        # global guard clauses
        return result