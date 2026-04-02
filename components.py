from dataclasses import dataclass
from typing import List, Dict, Any, ClassVar, Set, Tuple
from typing import List, Union
import re

class FunctionTranslationException(Exception):
    pass

@dataclass(frozen=True, slots=True)
class Token:
    pass

@dataclass(frozen=True, slots=True)
class OperatorToken(Token):
    value: str

@dataclass(frozen=True, slots=True)
class OpeningRoundBracketToken(Token): # No need value as they are only used for parsing and translation, not for final output
    pass

@dataclass(frozen=True, slots=True)
class ClosingRoundBracketToken(Token):
    pass

@dataclass(frozen=True, slots=True)
class OpeningSquigglyBracketToken(Token):
    pass

@dataclass(frozen=True, slots=True)
class ClosingSquigglyBracketToken(Token):
    pass

@dataclass(frozen=True, slots=True)
class TermToken(Token):
    value: str

    @property
    def is_set(self) -> bool:
        return self.value in PatGlobal.sets

@dataclass(frozen=True, slots=True)
class CommaToken(Token):
    pass

@dataclass(frozen=True, slots=True)
class TranslatableToken(Token):
    value: str

    def get_translation(self) -> str:
        raise NotImplementedError("This method should be implemented by subclasses of TranslatableToken")

@dataclass(frozen=True, slots=True)
class TranslatedToken(TranslatableToken):
    value: str

    def get_translation(self) -> str:
        return self.value

@dataclass(frozen=True, slots=True)
class PlainTextToken(TranslatableToken):
    value: str

    def get_translation(self) -> str:
        return self.value

@dataclass(frozen=True, slots=True)
class SetToken(TranslatableToken):
    value: List[Union[TermToken, "SetToken"]]
    name: str = ""

    def __post_init__(self):
        PatGlobal.add_enum([term.value for term, _ in self.flatten_with_level()])

    def flatten_with_level(self, current_level: int = 1) -> List[Tuple["TermToken", int]]:
        result: List[Tuple["TermToken", int]] = []
        for item in self.value:
            if isinstance(item, TermToken):
                result.append((item, current_level))
            elif isinstance(item, SetToken):
                result.extend(item.flatten_with_level(current_level + 1))
            else:
                raise TypeError(f"Invalid item in SetToken: {item}")
        return result
    
    def get_translation(self) -> str:
        flattened = self.flatten_with_level()

        seen = {}
        for term, _ in flattened:
            if term.value not in seen:
                seen[term.value] = len(seen)

        enum_names = list(seen.keys())

        mask_expr = " | ".join(f"{name}_BIT" for name in enum_names)
        return f"var {self.name} = {mask_expr};"

@dataclass(frozen=True, slots=True)
class FunctionTypeToken(Token):
    parameters: str
    return_type: str

    @property
    def value(self) -> str:
        return f"({self.parameters}) -> {self.return_type}"

@dataclass(frozen=True, slots=True)
class FunctionDefinitionToken(TranslatableToken):
    func_name: str
    value: str

@dataclass(frozen=True, slots=True)
class FunctionCallToken(Token):
    value: str

    #got lazy
    def to_pat_call(self) -> str:
        """
        Converts 'func(param1, param2, ...)' into 'call(func, param1, param2, ...)'.
        """

        match = re.fullmatch(r'\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*)\)\s*', self.value)
        if not match:
            raise ValueError(f"Invalid function call expression: {self.value}")
        
        func_name, params = match.groups()
        params = [p.strip() for p in params.split(',')] if params.strip() else []
        return f"call({func_name}, {', '.join(params)})"

TokenT = Union[
    OperatorToken,
    OpeningRoundBracketToken,
    ClosingRoundBracketToken,
    OpeningSquigglyBracketToken,
    ClosingSquigglyBracketToken,
    TermToken,
    SetToken,
    CommaToken,
    TranslatedToken,
    FunctionTypeToken,
    FunctionCallToken,
]

@dataclass(frozen=True, slots=True)
class EventBAxiom:
    name: str
    predicate: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EventBAxiom":
        return EventBAxiom(
            name=data.get("name", ""),
            predicate=data.get("predicate", "")
        )


@dataclass(frozen=True, slots=True)
class EventBInvariant:
    name: str
    predicate: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EventBInvariant":
        return EventBInvariant(
            name=data.get("name", ""),
            predicate=data.get("predicate", "")
        )


@dataclass(frozen=True, slots=True)
class EventBGuard:
    name: str
    predicate: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EventBGuard":
        return EventBGuard(
            name=data.get("name", ""),
            predicate=data.get("predicate", "")
        )


@dataclass(frozen=True, slots=True)
class EventBAction:
    name: str
    assignment: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EventBAction":
        return EventBAction(
            name=data.get("name", ""),
            assignment=data.get("assignment", "")
        )

@dataclass(frozen=True, slots=True)
class EventBContext:

    name: str
    sets: List[str]
    constants: List[str]
    axioms: List[EventBAxiom]
    extends: List[str]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EventBContext":

        return EventBContext(
            name=data.get("CONTEXT", ""),
            sets=list(data.get("SETS", [])),
            constants=list(data.get("CONSTANTS", [])),
            axioms=[
                EventBAxiom.from_dict(ax)
                for ax in data.get("AXIOMS", [])
            ],
            extends=list(data.get("EXTENDS", []))
        )

    def __str__(self):

        return (
            f"Context: {self.name}\n"
            f"  Sets: {self.sets}\n"
            f"  Constants: {self.constants}\n"
            f"  Axioms: {[ax.predicate for ax in self.axioms]}\n"
            f"  Extends: {self.extends}"
        )

@dataclass(frozen=True, slots=True)
class EventBEvent:

    name: str
    refines: List[str]
    any: List[str]
    where: List[EventBGuard]
    withs: List[str]
    then: List[EventBAction]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EventBEvent":

        return EventBEvent(
            name=data.get("event_name", ""),
            refines=list(data.get("REFINES", [])),
            any=list(data.get("ANY", [])),
            where=[
                EventBGuard.from_dict(g)
                for g in data.get("WHERE", [])
            ],
            withs=list(data.get("WITH", [])),
            then=[
                EventBAction.from_dict(a)
                for a in data.get("THEN", [])
            ]
        )
    
    def  is_initialisation(self) -> bool:
        return self.name.lower() == "initialisation"

    def __str__(self):

        return (
            f"Event: {self.name}\n"
            f"  ANY: {self.any}\n"
            f"  Guards: {[g.predicate for g in self.where]}\n"
            f"  Actions: {[a.assignment for a in self.then]}"
        )

@dataclass(frozen=True, slots=True)
class EventBMachine:

    name: str
    refines: List[str]
    sees: List[str]
    variables: List[str]
    invariants: List[EventBInvariant]
    events: List[EventBEvent]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EventBMachine":

        return EventBMachine(
            name=data.get("MACHINE", ""),
            refines=list(data.get("REFINES", [])),
            sees=list(data.get("SEES", [])),
            variables=list(data.get("VARIABLES", [])),
            invariants=[
                EventBInvariant.from_dict(inv)
                for inv in data.get("INVARIANTS", [])
            ],
            events=[
                EventBEvent.from_dict(ev)
                for ev in data.get("EVENTS", [])
            ]
        )

    def __str__(self):

        return (
            f"Machine: {self.name}\n"
            f"  Refines: {self.refines}\n"
            f"  Sees: {self.sees}\n"
            f"  Variables: {self.variables}\n"
            f"  Invariants: {[inv.predicate for inv in self.invariants]}\n"
            f"  Events:\n" +
            "\n".join(str(ev) for ev in self.events)
        )

@dataclass(frozen=True, slots=True)
class PatGlobal:
    """
    This class serves as a global registry for enums, variables, defines, and custom functions that are encountered during the translation process.
    Not sure if this will be the best way to handle this, but it allows us to keep track of these elements and ensure that they are defined in the generated code as needed.
    """

    @dataclass
    class FunctionInfo:
        definition: List[str]
        arity: int

    assertCount: ClassVar[int] = 0
    enums: ClassVar[Set[str]] = set() # A global enum is used as enum {blue, red}; enume {yellow, green}; red == green when it really shouldnt
    sets: ClassVar[Set[str]] = set() # so we know which terms are sets and not just normal terms
    functions: ClassVar[Dict[str, FunctionInfo]] = {}
    variables: ClassVar[Set[str]] = set()
    constants: ClassVar[Set[str]] = set()
    is_ai_used: ClassVar[bool] = False

    @classmethod
    def increment_assert_count(cls) -> int:
        cls.assertCount += 1
        return cls.assertCount
    
    @classmethod
    def add_enum(cls, elements :List[str]) -> None:
        for element in elements:
            cls.enums.add(element)

    @classmethod
    def add_variable(cls, var_name: str) -> None:
        cls.variables.add(var_name)

    @classmethod
    def add_constant(cls, const_name: str) -> None:
        cls.constants.add(const_name)
    
    @classmethod
    def add_set(cls, set_name: str) -> None:
        if len(set_name) == 0:
            return
        cls.sets.add(set_name)

    @classmethod
    def add_function_definition(
        cls,
        func_name: str,
        definition: str
    ) -> None:

        if func_name not in cls.functions:
            arity = cls._extract_arity(definition)
            cls.functions[func_name] = cls.FunctionInfo(definition=[definition], arity=arity)

        info = cls.functions[func_name]
        info.definition.append(definition)

    @classmethod
    def _extract_arity(cls, signature: str) -> int:
        signature = signature.replace("->", "→")
        match = re.search(r'∈\s*(.*?)\s*→', signature)
        if not match:
            return -1;

        domain = match.group(1).strip()

        parts = re.split(r'[×x]', domain)

        return len([p for p in parts if p.strip()])
    
    @classmethod
    def print_globals(cls) -> None:
        print(f"Enums: {cls.enums}")
        print(f"Variables: {cls.variables}")
        print(f"Sets: {cls.sets}")
        print(f"Functions: {cls.functions}")

    @classmethod
    def functions_to_string(cls) -> str:
        result = []
        for func_name, info in cls.functions.items():
            result.append(f"Function: {func_name} has an arity of {info.arity} where:\n")
            for definition in info.definition:
                result.append(f"  {definition}\n")
        return "".join(result)
    
    @classmethod
    def set_ai_used(cls) -> None:
        cls.is_ai_used = True
    
    @classmethod
    def get_ai_used(cls) -> bool:
        return cls.is_ai_used