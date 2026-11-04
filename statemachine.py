"""A State machine DSL

This module defines a state machine DSL metaclass that can be used
to create objects implementing a state machine
"""

from collections import defaultdict
from types import MappingProxyType

ATTRS_TO_POP = (
    ("initial", "Missing attribute 'initial' indicating the initial state"),
    ("states", "Missing attribute 'states' indicating the allowed states"),
    (
        "transitions",
        "Missing attribute 'transitions' representing the event transitions",
    ),
)


class StateMachine(type):
    """A state machine metaclass"""

    def __new__(metacls, name, bases, namespace):

        machine = {
            attr: _pop_attr(namespace, attr, err_msg) for attr, err_msg in ATTRS_TO_POP
        }

        if machine["initial"] not in machine["states"]:
            raise ValueError(
                f"initial state '{machine['initial']}' missing from list of states"
            )

        cls = super().__new__(metacls, name, bases, namespace)

        machine["transitions_by_state"] = _invert_transitions(machine["transitions"])

        cls._machine = _readonly_machine(machine)

        cls.state = property(_make_state_getter(cls._machine))
        cls.transition = _make_transition_method(cls._machine)
        return cls


def _pop_attr(namespace, name, err_msg):
    """Pop required attribute from namespace"""
    try:
        return namespace.pop(name)
    except KeyError as exc:
        raise TypeError(err_msg) from exc


def _make_state_getter(machine):
    """Create a state getter method"""

    def get_state(self):
        """Indicate current state"""
        try:
            return self.__state
        except AttributeError:
            self.__state = machine["initial"]
            return self.__state

    return get_state


def _make_transition_method(machine):
    """Uses machine state to create a state transition method"""

    def transition(self, event):
        """Update current state based on the event"""
        current_state = self.state
        try:
            self.__state = machine["transitions_by_state"][current_state][event]
        except KeyError:
            raise ValueError(f"{event} is not a valid event for {current_state}")

    return transition


def _readonly_machine(machine):
    """Create read-only version of the state machine"""
    return MappingProxyType(
        {
            "states": frozenset(machine["states"]),
            "events": frozenset(machine["transitions"]),
            "transitions_by_event": MappingProxyType(
                {
                    e: MappingProxyType(dict(machine["transitions"][e]))
                    for e in machine["transitions"]
                }
            ),
            "transitions_by_state": MappingProxyType(
                {
                    state: MappingProxyType(
                        dict(machine["transitions_by_state"][state])
                    )
                    for state in machine["transitions_by_state"]
                }
            ),
            "initial": machine["initial"],
        }
    )


def _invert_transitions(transitions):
    inverted = defaultdict(dict)
    for event, event_transitions in transitions.items():
        for src, dest in event_transitions.items():
            inverted[src][event] = dest
    return inverted
