# State Machine DSL — MVP Specification

## 1. Project Overview

A single-file Python library (`statemachine.py`) that lets other
developers declare finite state machines as plain data in a class
body. A metaclass (`StateMachine`) compiles the declaration at
class-creation time into an optimized runtime API, then strips the raw
declaration from the class.

**Target user:** Python application developers who need small,
deterministic FSMs (workflow steps, UI flows, device controllers) and
want the machine's invariants enforced at class-creation time, not at
runtime.

**Canonical example (acceptance "hello world"):** `Door` with states
`closed | open | locked` and events `open | close | lock | unlock`.

---

## 2. Scope

### In scope (MVP)
- Flat states (no hierarchy).
- Named events with deterministic transitions.
- Per-instance current state.
- Runtime API: `.state`, `.transition(event)`, `.can(event)`,
  `.reset()`.
- Hook auto-discovery: `on_enter_<state>`, `on_exit_<state>`,
  `on_transition_<event>`.
- Compile-time validation of the declaration.
- Compile-time validation of hook names (typos caught early).
- Private introspection dict `_machine` describing the compiled graph.
- Test file + `__main__` end-to-end demo.

### Out of scope (post-MVP / stretch)
- Guards, conditional transitions.
- Hierarchical / sub-states.
- Serialization (`to_dict()` / `from_dict()`).
- Graphviz DOT export.
- Async transitions.
- Thread safety.
- Hook signature introspection at compile time.
- Inheritance / extension of a compiled machine.
- Coverage targets.

---

## 3. Use Cases

### UC-1 — Declare and use a `Door` machine
A developer writes a class with `states`, `initial`, `transitions`,
and a few hooks, instantiates it, fires events, and observes state
changes and hook invocations.

### UC-2 — Query legality before firing
A caller uses `.can(event)` to decide whether an action is currently
available (e.g., to enable/disable a UI button) without mutating
state.

### UC-3 — Reset to a known baseline
A caller resets an instance to the machine's `initial` state (e.g.,
between tests or after an error) without firing hooks.

### UC-4 — Catch declaration bugs at class-creation time
A typo in a state name, a missing `initial`, an unreachable state, or
a misspelled hook raises immediately when the module is imported — not
deep in application logic.

### UC-5 — Introspect the compiled machine
Tooling / tests read `Door._machine` to enumerate states, events, and
legal transitions without touching private state.

---

## 4. Functional Requirements

### FR-1 — User-facing source language
A class uses `metaclass=StateMachine` and declares exactly three class
attributes:
- `states`: `list[str]` (non-empty)
- `initial`: `str` (must be in `states`)
- `transitions`: `dict[str event, dict[str source_state, str
  target_state]]`

All state and event names are Python `str`. Non-`str` values are a
compile-time `ValueError`.

Hooks are ordinary methods with names of the form `on_enter_<state>`,
`on_exit_<state>`, or `on_transition_<event>`.

### FR-2 — Compilation pipeline (metaclass)
1. **Parse** — extract `states`, `initial`, `transitions` from the
   class namespace.
2. **Validate** — see FR-3.
3. **Optimize** —
   - Build the transition table `dict[event, dict[source, target]]`
     (already flat; kept as-is).
   - Pre-index `valid_events[state] → frozenset[event names]`.
4. **Inject** —
   - `.state` (read-only property)
   - `.transition(event)` (method)
   - `.can(event)` (method, returns `bool`)
   - `.reset()` (method)
5. **Strip** — delete `states`, `initial`, `transitions` from the
   class namespace (accessing `Door.states` etc. raises
   `AttributeError`).
6. **Introspect** — set `cls._machine` to a plain dict: ```python {
   'states': tuple(states), 'initial': initial, 'transitions':
   dict_of_dicts_copy, 'valid_events': dict[state, frozenset(event
   names)], } ``` `_machine` describes only the graph; hooks are
   discoverable via normal `getattr(cls, name, None)`.

### FR-3 — Compile-time validation
All errors raise `ValueError` at class creation. The following checks run in order:

| # | Rule | Example message |
|---|---|---|
| 1 | `states` is a non-empty list of `str` | `ValueError: 'states' must be a non-empty list of str` |
| 2 | `initial` is a `str` present in `states` | `ValueError: initial state 'foo' not in states` |
| 3 | All event names are `str` | `ValueError: event names must be str` |
| 4 | All source / target states in `transitions` exist in `states` | `ValueError: transition 'open' references unknown source state 'jar'` / `ValueError: transition 'open' references unknown target state 'ajar'` |
| 5 | Every event has at least one source→target mapping | `ValueError: event 'noop' has no source→target mappings` |
| 6 | Every state except terminal ones is reachable from `initial` via a directed walk on the transition graph | `ValueError: state 'jammed' is unreachable from initial state 'closed'` |
| 7 | `initial` has at least one outgoing transition | `ValueError: initial state 'closed' has no outgoing transitions` |
| 8 | Every hook name refers to a real state or event | `ValueError: hook 'on_enter_jammed' references unknown state 'jammed'` / `ValueError: hook 'on_transition_teleport' references unknown event 'teleport'` |
| 9 | Reserved API names (`state`, `transition`, `can`, `reset`, `_machine`) declared by the user are silently replaced by the injected versions (MVP choice; see Risks) | — |

Notes on reachability: "reachable" = there is a directed path from
`initial` to that state following transition edges. `initial` is
trivially reachable. A state with only a self-loop but no path from
`initial` is unreachable and raises. Terminal states (no outgoing
transitions) are legal — only `initial` must have ≥ 1 outgoing
transition.

Notes on duplicates: dict literal syntax cannot express duplicate
`(event, source)` pairs (last wins silently); the "no duplicate
events" rule is dropped for MVP.

### FR-4 — Runtime API

**`.state` (property, read-only)**
- Returns the current state as `str`.
- Assignment raises `AttributeError`.
- First access lazily seeds the state to `initial` (no `__init__`
  magic). *Design note: subject to change post-MVP.*

**`.transition(event)`**
- Signature: `transition(self, event: str) -> None`.
- Raises `ValueError` if `event` is not in `transitions` (`event
  '<name>' is not a valid event`).
- Raises `ValueError` if `event` is valid globally but not legal from
  the current state (`event 'open' is not valid in state 'open'`).
- On success: updates state, runs hooks (see FR-5), returns `None`.

**`.can(event) -> bool`**
- Raises `ValueError` if `event` is not in `transitions` (unknown
  event = caller typo).
- Returns `True` if the event is legal from the current state, `False`
  otherwise (known event, wrong state).
- Never mutates state, never runs hooks.

**`.reset() -> None`**
- Silently sets state back to `initial`.
- Does not fire any hooks.
- If already in `initial`, this is a no-op.

### FR-5 — Hook semantics
- Discovered at compile time via `getattr` on `on_enter_<state>`,
  `on_exit_<state>`, `on_transition_<event>`. Missing hooks are
  silently skipped.
- Hook signature: takes only `self`. No compile-time signature check;
  incorrect signatures surface as `TypeError` at transition time.
- Invocation order for a state-changing transition `X: from → to`:
  1. `on_exit_<from>` (if defined)
  2. `on_transition_<X>` (if defined)
  3. `on_enter_<to>` (if defined)
- **Self-loop transitions** (`from == to`): fire only
  `on_transition_<X>`; skip enter/exit hooks since the state does not
  change.
- `self.state` inside hooks:
  - `on_exit_*` sees the **old** state.
  - `on_transition_*` sees the **new** state (state is updated before
    hooks run). *(documented gotcha)*
  - `on_enter_*` sees the **new** state.

### FR-6 — Inheritance
Not supported. A subclass inherits the parent's compiled machine
unchanged. Redefining `states` / `initial` / `transitions` in a
subclass is **unsupported** (undefined behavior; may be restricted in
a future version). Subclasses may add or override hooks.

### FR-7 — `__main__` demo
Running `python statemachine.py` executes a `Door` walkthrough:
construct instance, fire each event, demonstrate `.can()`, `.reset()`,
and print hook call order. Serves as the end-to-end acceptance demo.

---

## 5. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Language / runtime** | Python **3.8+**, standard library only (no third-party deps). |
| **Distribution** | Single-file module `statemachine.py`. No packaging, no `pyproject.toml`. |
| **API surface** | Public: `StateMachine` (metaclass) and the four members `.state`, `.transition`, `.can`, `.reset`. Private: `cls._machine`, `cls._hooks` (internal). |
| **Failure model** | All declaration / typo errors surface at **class-creation time** as `ValueError`. Illegal event at runtime raises `ValueError`. Illegal attribute write raises `AttributeError`. |
| **Performance** | Hook lookup and validity checks are pre-computed at compile time; per-call work is O(1) dict lookups. No perf budget, but no obvious O(n) hot paths. |
| **State immutability** | Compiled machine (states / transitions / valid_events) is not mutated at runtime. |
| **Thread safety** | Out of scope for MVP. |
| **Testing** | A `test_statemachine.py` file exercising: happy-path Door flow, each compile-time validation error, `.can()` behaviors, `.reset()`, hook order, self-loop semantics, read-only `.state`, `_machine` introspection, method-name collision behavior. Runnable with `pytest`. No coverage target. |
| **Documentation** | Module docstring with the Door example + error-message table. No separate README required for MVP. |

---

## 6. Acceptance Criteria

- [ ] `statemachine.py` is a single file with no third-party imports.
- [ ] The `Door` example from this spec compiles and behaves exactly
      as described in FR-4 / FR-5.
- [ ] Each of the nine compile-time validation rules in FR-3 has at
      least one test asserting the specific `ValueError` message.
- [ ] `.can()` and `.transition()` both raise `ValueError` on unknown
      events; `.can()` returns `False` (not raise) on
      known-but-wrong-state events.
- [ ] `.reset()` does not fire hooks and does return to `initial`.
- [ ] Hook order for a state-changing transition is `exit → transition
      → enter`; self-loops fire only `on_transition_<event>`.
- [ ] `Door.states`, `Door.initial`, `Door.transitions` raise
      `AttributeError` after class creation; `Door._machine` exposes
      the four graph keys.
- [ ] `python statemachine.py` runs the `Door` demo end-to-end.
- [ ] `pytest test_statemachine.py` passes.

---

## 7. Risks & Open Items (flagged for post-MVP)

| Risk / open item | Notes |
|---|---|
| Lazy state seeding (no `__init__` magic) | **Subject to change.** Could be replaced by metaclass-wrapped `__init__` if edge cases emerge. |
| Method-name collisions: injected API silently overwrites user's `transition` / `can` / `reset` / `state` | Silent data loss; strongly recommend flipping to a compile-time `ValueError: '<name>' is reserved` post-MVP. |
| No hook signature validation at compile time | Wrong hook signature produces a `TypeError` at transition time. Consider `inspect.signature` check post-MVP. |
| `on_transition_<event>` sees the *new* state | Subtle; must be prominently documented. |
| No inheritance / extension | Re-declaring machine in a subclass is undefined behavior. |
| Hook-name typos that match nothing in the machine already raise (good), but valid-state typos in *transition targets* require the user to read the error message carefully. | Message quality matters. |

---
