from enum import Enum, auto
from typing import List
from components import PatGlobal
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

class TranslationPurpose(Enum):
    CONTEXT = auto()
    MACHINE_VAR = auto()
    MACHINE_CONDITION = auto()
    MACHINE_ACTION_THEN = auto()

class TranslationHandler:
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        raise NotImplementedError


class PartitionTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        if purpose != TranslationPurpose.CONTEXT:
            raise ValueError("Partition only valid in CONTEXT")

        elements = []
        while len(stack) > 1:
            elements.append(stack.pop())
        elements.reverse()

        enum_name = stack.pop()
        PatGlobal.add_enum(enum_name)

        return f"enum {{{','.join(elements)}}};\n"

class AssignmentTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        value = stack.pop()
        name = stack.pop()

        if purpose == TranslationPurpose.CONTEXT:
            return f"#define {name} {value};\n"

        if purpose == TranslationPurpose.MACHINE_VAR:
            PatGlobal.add_variable(name)
            return f"var {name} = {value};\n"

        if purpose == TranslationPurpose.MACHINE_ACTION_THEN:
            return f"{name} = {value};\n"

        raise ValueError("Invalid purpose for assignment")

class EqualityTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()

        if purpose == TranslationPurpose.CONTEXT:
            return f"#define {left} {right};\n"

        if purpose == TranslationPurpose.MACHINE_CONDITION:
            return f"{left} == {right}"

        raise ValueError("Invalid purpose for equality")

def comparison_handler(stack: List[str], purpose, symbol):
    right = stack.pop()
    left = stack.pop()

    if purpose == TranslationPurpose.MACHINE_CONDITION:
        return f"{left} {symbol} {right}"

    if purpose == TranslationPurpose.CONTEXT:
        count = PatGlobal.increment_define_count()
        return (
            f"#define {left} 0;// Please change the value here\n"
            f"#define INVARIANT{count} {left} {symbol} {right};\n"
            f"#assert P() |= []INVARIANT{count};\n"
        )

    raise ValueError("Invalid purpose for comparison operator")


class GreaterTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        return comparison_handler(stack, purpose, ">")


class LessTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        return comparison_handler(stack, purpose, "<")


class GreaterEqualTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        return comparison_handler(stack, purpose, ">=")


class LessEqualTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        return comparison_handler(stack, purpose, "<=")

class PlusTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        evaluated = try_eval_binary(left, right, operator.add)
        result = evaluated if evaluated is not None else f"({left} + {right})"
        return result


class MinusTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        evaluated = try_eval_binary(left, right, operator.sub)
        result = evaluated if evaluated is not None else f"({left} - {right})"
        return result


class MultiplyTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        evaluated = try_eval_binary(left, right, operator.mul)
        result = evaluated if evaluated is not None else f"({left} * {right})"
        return result


class DivideTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        evaluated = try_eval_binary(left, right, operator.floordiv)
        result = evaluated if evaluated is not None else f"({left} / {right})"
        return result

class ImplicationTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        result = f"(!({left}) || ({right}))"
        return result

class OrTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        result = f"({left} || {right})"
        return result

class AndTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        result = f"({left} && {right})"
        return result

class NotTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        operand = stack.pop()
        result = f"!({operand})"
        return result
    
class MembershipTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose) -> str:
        right = stack.pop()
        left = stack.pop()
        if right == "ℕ":
            result = f"({left} >= 0)"
        else:
            raise ValueError(f"Unsupported set for membership: {right}")
        return result