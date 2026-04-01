from enum import Enum, auto
from typing import List
from components import *
import operator

def try_eval_binary(left: str, right: str, op):
    try:
        if isinstance(left, TokenT) or isinstance(right, TokenT):
            return None
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

def pop_value(stack: List[TokenT]) -> str|TokenT:
    token = stack.pop()
    if isinstance(token, TranslatedToken):
        return token.value
    return token # for more complicated stuff


def push_translated(stack: List[TokenT], value):
    if isinstance(value, str):
        stack.append(TranslatedToken(value))
    elif isinstance(value, TranslatableToken):
        stack.append(value)
    else:
        raise ValueError("Value must be either a string or a TranslatableToken")

class PartitionTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        if context != TranslationContext.CONTEXT:
            raise ValueError("partition only supported in CONTEXT")
        
        elements: List[str] = []
        
        while len(stack) > 1:
            top = stack.pop()
            
            if isinstance(top, SetToken):
                flattened_with_levels = top.flatten_with_level()
                for term, level in flattened_with_levels:
                    if level != 1:
                        raise ValueError("Nested sets not supported in partition")
                    elements.append(term.value)
            else:
                term = pop_value([top])
                elements.append(term)

        set_name = pop_value(stack)
        
        if not isinstance(set_name, str):
            raise ValueError("Expected set name to be a string (TranslatedToken value)")

        PatGlobal.add_enum(elements)
        # result = f"{set_name} = [{','.join(elements)}];\n"
        result = SetToken(value=[TermToken(e) for e in elements], name=set_name)
        push_translated(stack, result)

class AssignmentTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
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
            if isinstance(value, FunctionCallToken):
                value = value.to_pat_call()
            push_translated(stack, f"{name} = {value};\n")
            return

        raise ValueError("Invalid context for assignment")

class EqualityTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        if context == TranslationContext.CONTEXT:
            if isinstance(left, FunctionCallToken):
                raise FunctionTranslationException(left.value.split('(')[0])
            push_translated(stack, f"#define {left} {right};\n")
            return
        if context == TranslationContext.MACHINE_CONDITION:
            if isinstance(right, FunctionCallToken):
                right = right.to_pat_call()
            push_translated(stack, f"{left} == {right}")
            return

        raise ValueError("Invalid context for equality")

class NotEqualTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        if context == TranslationContext.MACHINE_CONDITION:
            if isinstance(right, FunctionCallToken):
                right = right.to_pat_call()

            push_translated(stack, f"{left} != {right}")
            return

def comparison_handler(stack: List[TokenT], context, symbol):
    right = pop_value(stack)
    left = pop_value(stack)

    if context == TranslationContext.MACHINE_CONDITION:
        push_translated(stack, f"{left} {symbol} {right}")
        return

    if context == TranslationContext.CONTEXT:

        count = PatGlobal.increment_assert_count()

        result = (
            f"#define {left} 0;// Please change the value here\n"
            f"#define INV{count} {left} {symbol} {right};\n"
            f"#assert P() |= []INV{count};\n"
        )

        push_translated(stack, result)
        return

    raise ValueError("Invalid context for comparison operator")

class GreaterTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        comparison_handler(stack, context, ">")

class LessTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        comparison_handler(stack, context, "<")

class GreaterEqualTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        comparison_handler(stack, context, ">=")

class LessEqualTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        comparison_handler(stack, context, "<=")

class PlusTranslation(TranslationHandler):

    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:

        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.add)

        result = evaluated if evaluated is not None else f"({left} + {right})"

        push_translated(stack, result)

class MinusTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.sub)
        result = evaluated if evaluated is not None else f"({left} - {right})"

        push_translated(stack, result)

class MultiplyTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.mul)
        result = evaluated if evaluated is not None else f"({left} * {right})"

        push_translated(stack, result)

class DivideTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        evaluated = try_eval_binary(left, right, operator.floordiv)
        result = evaluated if evaluated is not None else f"({left} / {right})"

        push_translated(stack, result)

class ImplicationTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        result = f"(!({left}) || ({right}))"

        push_translated(stack, result)

class OrTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        push_translated(stack, f"({left} || {right})")

class AndTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        push_translated(stack, f"({left} && {right})")

class NotTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        operand = pop_value(stack)

        push_translated(stack, f"!({operand})")

class MembershipTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        if left not in PatGlobal.variables and left not in PatGlobal.constants:
            stack.append(left)
            stack.append(right)
            raise NotImplementedError(f"Left operand of membership must be a variable or constant, got {left}")

        if right == "ℕ":
            result = f"({left} >= 0)"
        elif right == "ℕ1":
            result = f"({left} > 0)"
        elif right == "ℤ":
            result = "true"
        elif right == "BOOL":
            result = f"({left} == true || {left} == false)"
        elif isinstance(right, FunctionTypeToken):
            raise FunctionTranslationException(left)
        else:
            raise ValueError(f"Unsupported set for membership: {right}")
        push_translated(stack, result)

class TypedMembershipTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)

        result = f"var {left} = 0;  // Please change the value and type here, expected type: {right}"
        push_translated(stack, result)

class FunctionTranslation(TranslationHandler):
    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        right = pop_value(stack)
        left = pop_value(stack)
        stack.append(FunctionTypeToken(return_type=right, parameters=[left]))

class FunctionCallTranslation(TranslationHandler):
    def __init__(self, func_name: str = ""):
        self.func_name = func_name

    def translate(self, stack: List[TokenT], context: TranslationContext) -> None:
        info = PatGlobal.functions.get(self.func_name)
        arity = info.arity if info else -1
        args = [pop_value(stack) for _ in range(arity)]
        print(f"Translating function call: {self.func_name} with args {args}")
        result = f"{self.func_name}({', '.join(reversed(args))})"
        stack.append(FunctionCallToken(result))