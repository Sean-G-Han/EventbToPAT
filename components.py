from dataclasses import dataclass
from typing import List, Dict, Any, ClassVar, Set, Tuple
from typing import List, Union

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

@dataclass(frozen=True, slots=True)
class SetToken(Token):
    value: List[Union[TermToken, "SetToken"]]

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

@dataclass(frozen=True, slots=True)
class CommaToken(Token):
    pass

@dataclass(frozen=True, slots=True)
class TranslatedToken(Token):
    value: str

@dataclass(frozen=True, slots=True)
class FunctionTypeToken(Token):
    return_type: str
    parameters: List[str]

@dataclass(frozen=True, slots=True)
class FunctionToken(Token):
    value: str
    functionType: FunctionTypeToken
    logic: any # Not decided yet... (Please help)


@dataclass(frozen=True, slots=True)
class FunctionCallToken(Token):
    value: str

TokenT = Union[
    OperatorToken,
    OpeningRoundBracketToken,
    ClosingRoundBracketToken,
    OpeningSquigglyBracketToken,
    ClosingSquigglyBracketToken,
    FunctionToken,
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
class CustomParameterInfo:
    name: str
    type: str

@dataclass(frozen=True, slots=True) 
class CustomFunctionInfo:
    function_name: str
    parameters: Set[CustomParameterInfo]
    return_type: str
    logic: any

@dataclass(frozen=True, slots=True)
class PatGlobal:
    """
    This class serves as a global registry for enums, variables, defines, and custom functions that are encountered during the translation process.
    Not sure if this will be the best way to handle this, but it allows us to keep track of these elements and ensure that they are defined in the generated code as needed.
    """
    assertCount: ClassVar[int] = 0
    paramCount: ClassVar[int] = 0
    enums: ClassVar[Dict[str, Set[str]]] = {} # functions as mathematical sets
    variables: ClassVar[Set[str]] = set()
    defines: ClassVar[Set[str]] = set()
    customFunctions: ClassVar[Dict[str, CustomFunctionInfo]] = {}

    @classmethod
    def increment_assert_count(cls) -> int:
        cls.assertCount += 1
        return cls.assertCount
    
    @classmethod
    def increment_parameter_count(cls) -> int:
        cls.paramCount += 1
        return cls.paramCount
    
    @classmethod
    def add_enum(cls, enum_name: str, elements :List[str]) -> None:
        cls.enums[enum_name] = set(elements)

    @classmethod
    def has_enum(cls, enum_name: str) -> bool:
        return enum_name in cls.enums

    @classmethod
    def add_variable(cls, var_name: str) -> None:
        cls.variables.add(var_name)

    @classmethod
    def has_variable(cls, var_name: str) -> bool:
        return var_name in cls.variables
    
    @classmethod
    def add_define(cls, define_name: str) -> None:
        cls.defines.add(define_name)
    
    @classmethod
    def has_define(cls, define_name: str) -> bool:
        return define_name in cls.defines
    
    @classmethod
    def print_globals(cls) -> None:
        print(f"Enums: {cls.enums}")
        print(f"Variables: {cls.variables}")
        print(f"Defines: {cls.defines}")

    @classmethod
    def add_custom_function(cls, func_info: CustomFunctionInfo) -> None:
        cls.customFunctions[func_info.function_name] = func_info
    
    @classmethod
    def is_custom_function(cls, func_name: str) -> bool:
        return func_name in cls.customFunctions