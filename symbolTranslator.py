from enum import Enum, auto
from typing import List
from components import PatGlobal
import operator

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
    MACHINE_INVARIANT = auto()

class TranslationHandler:
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        raise NotImplementedError

class PartitionTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        elements = []
        while len(stack) > 1:
            elements.append(stack.pop())
        elements.reverse()
        enum_name = stack.pop()
        PatGlobal.add_enum(enum_name)
        return f"enum {{{','.join(elements)}}};\n"

class AssignmentTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        value = stack.pop()      # right operand
        name = stack.pop()       # left operand

        if purpose == TranslationPurpose.MACHINE_VAR:
            PatGlobal.add_variable(name)
            return f"var {name} = {value};\n"
        return f"#define {name} {value};\n"


class EqualityTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        value = stack.pop()
        name = stack.pop()

        if purpose == TranslationPurpose.CONTEXT:
            return f"#define {name} {value};\n"

        elif purpose == TranslationPurpose.MACHINE_INVARIANT:
            count = PatGlobal.increment_define_count()
            return (
                f"#define INVARIANT{count} {name} == {value};\n"
                f"#assert P |= []INVARIANT{count};\n"
            )


class GreaterTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        value = stack.pop()
        name = stack.pop()
        count = PatGlobal.increment_define_count()

        return (
            f"#define {name} {int(value) + 1};\n"
            f"#define INVARIANT{count} ({name} > {value});\n"
            f"#assert P |= []INVARIANT{count};\n"
        )


class LessTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        value = stack.pop()
        name = stack.pop()
        count = PatGlobal.increment_define_count()

        return (
            f"#define {name} {int(value) - 1};\n"
            f"#define INVARIANT{count} ({name} < {value});\n"
            f"#assert P |= []INVARIANT{count};\n"
        )


class GreaterEqualTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        value = stack.pop()
        name = stack.pop()
        count = PatGlobal.increment_define_count()

        return (
            f"#define {name} {int(value)};\n"
            f"#define INVARIANT{count} ({name} >= {value});\n"
            f"#assert P |= []INVARIANT{count};\n"
        )


class LessEqualTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        value = stack.pop()
        name = stack.pop()
        count = PatGlobal.increment_define_count()

        return (
            f"#define {name} {int(value)};\n"
            f"#define INVARIANT{count} ({name} <= {value});\n"
            f"#assert P |= []INVARIANT{count};\n"
        )

class PlusTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        right = stack.pop()
        left = stack.pop()

        evaluated = try_eval_binary(left, right, operator.add)
        if evaluated is not None:
            return evaluated

        return f"({left} + {right})"


class MinusTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        right = stack.pop()
        left = stack.pop()

        evaluated = try_eval_binary(left, right, operator.sub)
        if evaluated is not None:
            return evaluated

        return f"({left} - {right})"


class DivideTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        right = stack.pop()
        left = stack.pop()

        evaluated = try_eval_binary(left, right, operator.floordiv)
        if evaluated is not None:
            return evaluated

        return f"({left} / {right})"


class MultiplyTranslation(TranslationHandler):
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        right = stack.pop()
        left = stack.pop()

        evaluated = try_eval_binary(left, right, operator.mul)
        if evaluated is not None:
            return evaluated

        return f"({left} * {right})"