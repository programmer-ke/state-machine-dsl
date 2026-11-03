"""A State machine DSL"""


class StateMachine(type):
    def __new__(metacls, name, bases, namespace):

        try:
            initial_state = namespace.pop("initial")
        except KeyError:
            raise TypeError(f"Missing attribute 'initial' indicating the initial state")

        try:
            states = namespace.pop('states')
        except KeyError:
            raise TypeError(f"Missing attribute 'states' indicating list of states")

        if not initial_state in states:
            raise ValueError(f"initial state missing from list of states")

        cls = super().__new__(metacls, name, bases, namespace)

        def get_state(self):
            """Indicate current state"""
            if "_state" not in self.__dict__:
                self._state = initial_state
            return self._state

        cls.state = property(get_state)
        return cls
