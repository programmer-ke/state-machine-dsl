from statemachine import StateMachine


class Door(metaclass=StateMachine):
    states   = ['closed', 'open', 'locked']
    initial = "closed"


def test_reports_initial_state():
    door = Door()
    assert door.state == "closed"

    class StartsOpen(metaclass=StateMachine):
        states   = ['closed', 'open', 'locked']
        initial = "open"

    assert StartsOpen().state == "open"

    
