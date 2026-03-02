from dataclasses import dataclass
from typing import List
from syntaxTranslator import *
from components import *

@dataclass
class ContextTranslator:

    translator: SyntaxTranslator

    def __init__(self):
        self.translator = SyntaxTranslator(extra_functions=["partition"]) # Might need to add more functions as we go

    def translate(self, contexts: List[EventBContext]) -> str:

        output: List[str] = []
        global_guards: List[str] = []

        for ctx in contexts:
            for a in ctx.axioms:
                translation = self.translate_axiom(a)
                
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

    def translate_axiom(self, axiom: EventBAxiom) -> str:

        tokens = self.translator.classify_tokens(axiom.predicate)
        postfix = self.translator.to_postfix(tokens)

        if postfix[-1].type == TokenType.FUNCTION and postfix[-1].value == "partition":
            set_name = postfix[0].value
            elements = [t.value for t in postfix[1:-1]]
            return f"enum {set_name} {{{','.join(elements)}}};"

        stack = []

        for token in postfix:
            match token.type:
                case TokenType.TERM:
                    stack.append(token.value)

                case TokenType.OPERATOR:
                    print(f"Processing operator: {token.value} with stack: {stack}")
                    pat_op, arity, prec = SyntaxTranslator.OPERATORS[token.value]
                    if arity == 1:
                        operand = stack.pop()
                        stack.append(f"{pat_op}{operand}")
                    elif arity == 2:
                        right = stack.pop()
                        left = stack.pop()
                        stack.append(f"({left} {pat_op} {right})")

                case TokenType.FUNCTION:
                    args = stack.copy()
                    stack.clear()
                    stack.append(f"{token.value}({','.join(args)})")

        return stack[0]

    def translate_context(self, axioms: List[str]) -> List[List[str]]:
        return [self.translate_axiom(a) for a in axioms]
