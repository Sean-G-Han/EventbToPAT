from enum import Enum, auto
from typing import List
from components import PatGlobal, Token, TokenType
import operator


# ==========================================================
# Utility
# ==========================================================

def try_eval_binary(left: str, right: str, op):
    try:
        l = float(left)
        r = float(right)
        result = op(l, r)

        if result.is_integer():
            return str(int(result))
        return str(result)
    except ValueError:
        return None

class TranslationContext(Enum):
    CONTEXT = auto()
    MACHINE_VAR = auto()
    MACHINE_CONDITION = auto()
    MACHINE_ACTION_THEN = auto()

class TranslationHandler:
    def translate(self, stack: List[str], context: TranslationContext) -> str:
        raise NotImplementedError

def pop_value(stack: List[Token]) -> str|Token:
    token = stack.pop()
    if token.type == TokenType.TRANSLATED:
        return token.value
    return token # for more complicated stuff


def push_translated(stack: List[Token], value):
    stack.append(Token(TokenType.TRANSLATED, value))

class PartitionTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        if context != TranslationContext.CONTEXT:
            raise ValueError("Partition only valid in CONTEXT")
        elements = []

        while len(stack) > 1:
            elements.append(pop_value(stack))

        elements.reverse()
        enum_name = pop_value(stack)
        PatGlobal.add_enum(enum_name, elements)

        result = f"enum {{{','.join(elements)}}};\n"
        push_translated(stack, result)

class AssignmentTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        value = pop_value(stack)
        name = pop_value(stack)

        if context == TranslationContext.CONTEXT:
            push_translated(stack, f"#define {name} {value};\n")
            return

        if context == TranslationContext.MACHINE_VAR:
            PatGlobal.add_variable(name)
            push_translated(stack, f"var {name} = {value};\n")
            return

        if context == TranslationContext.MACHINE_ACTION_THEN:
            push_translated(stack, f"{name} = {value};\n")
            return

        raise ValueError("Invalid context for assignment")

class EqualityTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        if context == TranslationContext.CONTEXT:
            push_translated(stack, f"#define {left} {right};\n")
            return
        if context == TranslationContext.MACHINE_CONDITION:
            push_translated(stack, f"{left} == {right}")
            return

        raise ValueError("Invalid context for equality")

def comparison_handler(stack: List[Token], context, symbol):
    right = pop_value(stack)
    left = pop_value(stack)

    if context == TranslationContext.MACHINE_CONDITION:
        push_translated(stack, f"{left} {symbol} {right}")
        return

    if context == TranslationContext.CONTEXT:

        count = PatGlobal.increment_define_count()

        result = (
            f"#define {left} 0;// Please change the value here\n"
            f"#define INVARIANT{count} {left} {symbol} {right};\n"
            f"#assert P() |= []INVARIANT{count};\n"
        )

        push_translated(stack, result)
        return

    raise ValueError("Invalid context for comparison operator")

class GreaterTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        comparison_handler(stack, context, ">")

class LessTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        comparison_handler(stack, context, "<")

class GreaterEqualTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        comparison_handler(stack, context, ">=")

class LessEqualTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        comparison_handler(stack, context, "<=")

class PlusTranslation(TranslationHandler):

    def translate(self, stack: List[Token], context: TranslationContext) -> None:

        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.add)

        result = evaluated if evaluated is not None else f"({left} + {right})"

        push_translated(stack, result)

class MinusTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.sub)
        result = evaluated if evaluated is not None else f"({left} - {right})"

        push_translated(stack, result)

class MultiplyTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.mul)
        result = evaluated if evaluated is not None else f"({left} * {right})"

        push_translated(stack, result)

class DivideTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.floordiv)
        result = evaluated if evaluated is not None else f"({left} / {right})"

        push_translated(stack, result)

class ImplicationTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        result = f"(!({left}) || ({right}))"

        push_translated(stack, result)

class OrTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        push_translated(stack, f"({left} || {right})")

class AndTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        push_translated(stack, f"({left} && {right})")

class NotTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        operand = pop_value(stack)

        push_translated(stack, f"!({operand})")

class MembershipTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        if right == "ℕ":
            result = f"({left} >= 0)"
        elif right == "ℕ1":
            result = f"({left} > 0)"
        elif right == "ℤ":
            result = "true"
        elif right == "BOOL":
            result = f"({left} == true || {left} == false)"
        else:
            raise ValueError(f"Unsupported set for membership: {right}")
        push_translated(stack, result)

class FunctionTypeTranslation(TranslationHandler):
    def translate(self, stack: List[Token], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        result = f"({left} -> {right})"
        stack.append(Token(TokenType.FUNCTION_TYPE, result))