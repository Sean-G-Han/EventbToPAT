from dataclasses import dataclass
from typing import List, Dict, Any

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