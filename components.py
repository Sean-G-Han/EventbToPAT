class EventBContext:
    __slots__ = ['name', 'sets', 'constants', 'axioms', 'extends']

    def __init__(self, data):
        super().__setattr__('name', data.get("CONTEXT"))
        super().__setattr__('sets', data.get("SETS", []))
        super().__setattr__('constants', data.get("CONSTANTS", []))
        super().__setattr__('axioms', data.get("AXIOMS", []))
        super().__setattr__('extends', data.get("EXTENDS", []))

    def __setattr__(self, key, value):
        raise AttributeError("Immutable EventBContext")

    def __str__(self) -> str:
        sets_str = ', '.join(self.sets)
        const_str = ', '.join(self.constants)
        axioms_str = ', '.join(ax.get('predicate', '') for ax in self.axioms)
        extends_str = ', '.join(self.extends)
        return (f"Context: {self.name}\n"
                f"  Sets: [{sets_str}]\n"
                f"  Constants: [{const_str}]\n"
                f"  Axioms: [{axioms_str}]\n"
                f"  Extends: [{extends_str}]")


class EventBEvent:
    __slots__ = ['name', 'refines', 'any', 'where', 'withs', 'then']

    def __init__(self, data):
        super().__setattr__('name', data.get("event_name"))
        super().__setattr__('refines', data.get("REFINES", []))
        super().__setattr__('any', data.get("ANY", []))
        super().__setattr__('where', data.get("WHERE", []))
        super().__setattr__('withs', data.get("WITH", []))
        super().__setattr__('then', data.get("THEN", []))

    def __setattr__(self, key, value):
        raise AttributeError("Immutable EventBEvent")
    
    def __str__(self) -> str:
        guards = ', '.join(g.get('predicate', '') for g in self.where)
        actions = ', '.join(a.get('assignment', '') for a in self.then)
        any_vars = ', '.join(self.any)
        return (f"Event: {self.name}\n"
                f"  ANY: [{any_vars}]\n"
                f"  WHERE (Guards): [{guards}]\n"
                f"  THEN (Actions): [{actions}]")


class EventBMachine:
    __slots__ = ['name', 'refines', 'sees', 'variables', 'invariants', 'events']

    def __init__(self, data):
        super().__setattr__('name', data.get("MACHINE"))
        super().__setattr__('refines', data.get("REFINES", []))
        super().__setattr__('sees', data.get("SEES", []))
        super().__setattr__('variables', data.get("VARIABLES", []))
        super().__setattr__('invariants', data.get("INVARIANTS", []))
        super().__setattr__('events', [EventBEvent(ev) for ev in data.get("EVENTS", [])])

    def __setattr__(self, key, value):
        raise AttributeError("Immutable EventBMachine")
    
    def __str__(self) -> str:
        vars_str = ', '.join(self.variables)
        invs_str = ', '.join(inv.get('predicate', '') for inv in self.invariants)
        events_str = '\n'.join(str(ev) for ev in self.events)
        refines_str = ', '.join(self.refines)
        sees_str = ', '.join(self.sees)
        return (f"Machine: {self.name}\n"
                f"  Refines: [{refines_str}]\n"
                f"  Sees: [{sees_str}]\n"
                f"  Variables: [{vars_str}]\n"
                f"  Invariants: [{invs_str}]\n"
                f"  Events:\n{events_str}")