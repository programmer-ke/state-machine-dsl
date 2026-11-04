# todo

## US-1.3 — Move the Door by firing events


> As a developer, I want to fire a named event with `.transition(event)` and have the machine move to the target state, so that I can drive the door through its lifecycle.

### Scenario 1.3.1 — Fire one event and change state *(hardcoded single-entry transition table)*
```gherkin
Given a Door in state 'closed'
When I fire event 'open'
Then door.state == 'open'
```

### Scenario 1.3.2 — The full Door transition table works
```gherkin
Given a Door with transitions open/close/lock/unlock
When I fire a legal sequence of events
Then each event moves the door to the declared target state
```

### Scenario 1.3.3 — Unknown event is rejected
```gherkin
Given a Door in state 'closed'
When I call transition('teleport')
Then a ValueError "event 'teleport' is not a valid event" is raised
And the state is unchanged
```

### Scenario 1.3.4 — Known event that is illegal right now is rejected
```gherkin
Given a Door in state 'open'
When I call transition('open')
Then a ValueError "event 'open' is not valid in state 'open'" is raised
And the state is unchanged
```

---

## US-1.4 — React to transitions with hooks
**Status:** `todo**

> As a developer, I want `on_enter_<state>`, `on_exit_<state>` and `on_transition_<event>` methods to run automatically, so that I can attach side effects without touching the transition logic.

### Scenario 1.4.1 — `on_enter_<state>` fires on arrival *(hardcoded hook lookup for one hook)*
```gherkin
Given a Door defining on_enter_open
When I fire event 'open' from 'closed'
Then on_enter_open is called exactly once
```

### Scenario 1.4.2 — Hooks fire in exit → transition → enter order
```gherkin
Given a Door defining on_exit_closed, on_transition_open and on_enter_open
When I fire event 'open' from 'closed'
Then the hooks are invoked in the order: on_exit_closed, on_transition_open, on_enter_open
```

### Scenario 1.4.3 — Self-loops fire only the transition hook
```gherkin
Given a machine with a self-loop event and both enter and exit hooks for that state
When I fire the self-loop event
Then only on_transition_<event> runs
```

### Scenario 1.4.4 — Hooks observe the documented state view
```gherkin
Given a Door with hooks that record self.state
When I fire event 'open' from 'closed'
Then on_exit_closed sees 'closed', on_transition_open sees the updated state, and on_enter_open sees 'open'
```

---

## US-1.5 — Catch declaration mistakes at class creation


> As a developer, I want typos in my declaration to raise `ValueError` when the class is created, so that I never ship a broken machine into application logic.
> *(Shared with UC-4; only the checks a `Door` author meets are sliced here.)*

### Scenario 1.5.1 — `initial` must be one of the states
```gherkin
Given a declaration with initial = 'foo' not listed in states
When the class is created
Then ValueError "initial state 'foo' not in states" is raised
```

### Scenario 1.5.2 — Transition states must exist
```gherkin
Given a transition referencing source state 'jar' which is not declared
When the class is created
Then ValueError "transition 'open' references unknown source state 'jar'" is raised
```

### Scenario 1.5.3 — Hook names must refer to real states/events
```gherkin
Given a method named on_enter_jammed where 'jammed' is not a state
When the class is created
Then ValueError "hook 'on_enter_jammed' references unknown state 'jammed'" is raised
```

---

## US-1.6 — See the Door working end-to-end


> As a developer, I want `python statemachine.py` to walk the `Door` through its events and print hook calls, so that I have a runnable acceptance demo of the whole flow.

### Scenario 1.6.1 — `__main__` demo exercises the full UC-1 happy path
```gherkin
Given the completed statemachine.py
When I run python statemachine.py
Then the output shows the constructed Door, each fired event, the resulting state, and the hook call order
```

# in progress

## US-1.2 — Declare the machine as plain data

> As a developer, I want to declare `states`, `initial` and
> `transitions` in a class body with `metaclass=StateMachine`, so that
> I can describe any FSM as data instead of hand-written code.

### Scenario 1.2.1 — A `StateMachine` metaclass compiles the declaration
```gherkin
Given the canonical Door class from the spec declared with metaclass=StateMachine
When the class is created
Then Door() constructs successfully and door.state == 'closed'
```

### Scenario 1.2.2 — The compiled graph is introspectable
```gherkin
Given a compiled Door class
When I read Door._machine
Then it exposes states, initial, transitions and valid_events describing the graph
```

---

# done

## US-1.1 — See the Door's current state

> As a Python application developer, I want to instantiate a `Door`
> and read its current state, so that I can model a door's condition
> in code.

### Scenario 1.1.1 — A fresh Door reports its initial state *(hardcoded `Door` class)*
```gherkin
Given a module statemachine.py containing a hardcoded Door class with
  states ['closed','open','locked']
When I construct Door()
Then door.state == 'closed'
```

### Scenario 1.1.2 — The initial state honours the declaration
```gherkin
Given a Door declaration whose initial state is 'open'
When I construct the machine
Then the first read of .state == 'open'
```
