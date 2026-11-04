from statemachine import StateMachine


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
    required_keys = ["states", "events", "initial", "transitions"]
    for k in required_keys:
        assert k in door._machine
