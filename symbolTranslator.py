from enum import Enum, auto
from typing import List
from components import PatTranslaton

class TranslationPurpose(Enum):
    CONTEXT = auto()
    MACHINE_VAR = auto()

class TranslationHandler:
    def translate(self, stack: List[str], purpose: TranslationPurpose = None) -> str:
        raise NotImplementedError

class PartitionTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        return f"enum {{{','.join(stack[1:])}}};\n"

class EqualityTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        name = stack[-2]
        value = stack[-1]
        if purpose == TranslationPurpose.MACHINE_VAR:
            return f"var {name} = {value};\n"
        return f"#define {name} {value};\n"


class AssignmentTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        name = stack[-2]
        value = stack[-1]
        if purpose == TranslationPurpose.MACHINE_VAR:
            return f"var {name} = {value};\n"
        return f"#define {name} {value};\n"


class GreaterTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        name = stack[-2]
        value = stack[-1]
        count = PatTranslaton.increment_define_count()

        return (
            f"#define {name} {int(value) + 1};\n"
            f"#define GLOBAL_GUARD{count} ({name} > {value});\n"
            f"#assert GLOBAL_GUARD{count};\n"
        )


class LessTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        name = stack[-2]
        value = stack[-1]
        count = PatTranslaton.increment_define_count()

        return (
            f"#define {name} {int(value) - 1};\n"
            f"#define GLOBAL_GUARD{count} ({name} < {value});\n"
            f"#assert GLOBAL_GUARD{count};\n"
        )


class GreaterEqualTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        name = stack[-2]
        value = stack[-1]
        count = PatTranslaton.increment_define_count()

        return (
            f"#define {name} {int(value)};\n"
            f"#define GLOBAL_GUARD{count} ({name} >= {value});\n"
            f"#assert GLOBAL_GUARD{count};\n"
        )


class LessEqualTranslation(TranslationHandler):
    def translate(
        self,
        stack: List[str],
        purpose: TranslationPurpose = None
    ) -> str:
        name = stack[-2]
        value = stack[-1]
        count = PatTranslaton.increment_define_count()

        return (
            f"#define {name} {int(value)};\n"
            f"#define GLOBAL_GUARD{count} ({name} <= {value});\n"
            f"#assert GLOBAL_GUARD{count};\n"
        )