from statemachine import StateMachine, _invert_transitions


class Door(metaclass=StateMachine):
    states = ["closed", "open", "locked"]
    initial = "closed"
    transitions = {
        "open": {"closed": "open", "locked": "open"},
        "close": {"open": "closed", "locked": "closed"},
        "lock": {"closed": "locked"},
        "unlock": {"locked": "closed"},
    }


class StartsOpen(metaclass=StateMachine):
    states = ["closed", "open", "locked"]
    initial = "open"
    transitions = {
        "open": {"closed": "open", "locked": "open"},
        "close": {"open": "closed", "locked": "closed"},
        "lock": {"closed": "locked"},
        "unlock": {"locked": "closed"},
    }


def test_reports_initial_state():
    door = Door()
    assert door.state == "closed"
    assert StartsOpen().state == "open"


def test_machine_introspection():

    door = Door()
    required_keys = [
        "states",
        "events",
        "initial",
        "transitions_by_state",
        "transitions_by_event",
    ]
    for k in required_keys:
        assert k in door._machine


def test_inverting_transitions():
    by_event = {
        "open": {"closed": "open", "locked": "open"},
        "close": {"open": "closed", "locked": "closed"},
        "lock": {"closed": "locked"},
        "unlock": {"locked": "closed"},
    }

    by_state = {
        "closed": {"open": "open", "lock": "locked"},
        "locked": {"open": "open", "close": "closed", "unlock": "closed"},
        "open": {"close": "closed"},
    }

    assert _invert_transitions(by_event) == by_state


def test_can_transition_from_initial_state():
    door = Door()
    assert door.state == "closed"

    door.transition("open")

    assert door.state == "open"
