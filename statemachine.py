"""A State machine DSL

This module defines a state machine DSL metaclass that can be used
to create objects implementing a state machine
"""

from types import MappingProxyType, SimpleNamespace

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

        machine = SimpleNamespace(
            **{
                attr: _pop_attr(namespace, attr, err_msg)
                for attr, err_msg in ATTRS_TO_POP
            }
        )

        if machine.initial not in machine.states:
            raise ValueError(
                f"initial state '{machine.initial}' missing from list of states"
            )

        cls = super().__new__(metacls, name, bases, namespace)

        cls._machine = _readonly_machine(machine)

        cls.state = property(_make_state_getter(machine))
        return cls


def _pop_attr(namespace, name, err_msg):
    """Pop required attribute from namespace"""
    try:
        return namespace.pop(name)
    except KeyError as exc:
        raise TypeError(err_msg) from exc


def _make_state_getter(machine):
    """Create a state getter method"""

    def _get_state(self):
        """Indicate current state"""
        try:
            return self.__state
        except AttributeError:
            self.__state = machine.initial
            return self.__state

    return _get_state


def _readonly_machine(machine):
    """Create read-only version of the state machine"""
    return MappingProxyType(
        {
            "states": tuple(machine.states),
            "events": tuple(e for e in machine.transitions),
            "transitions": MappingProxyType(
                {
                    e: MappingProxyType(dict(machine.transitions[e]))
                    for e in machine.transitions
                }
            ),
            "initial": machine.initial,
        }
    )
