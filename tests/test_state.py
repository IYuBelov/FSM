# coding=utf-8
import pytest

from fsm.FSM import FSM, FSMError


class TestFysomStateTests:

    @pytest.fixture()
    def fsm(self):
        fsm = FSM({
            'initial': {'state': 'green'},
            'transitions': [
                {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                {'event': 'clear', 'src': 'yellow', 'dst': 'green'},
                {'event': 'warm', 'src': 'green', 'dst': 'blue'}
            ]
        })
        return fsm

    def test_is_state_should_succeed_for_initial_state(self, fsm):
        assert fsm.getCurrentState() == 'green'

    def test_identity_transition_should_not_be_allowed_by_default(self, fsm):
        assert not fsm.can('clear')
        assert not fsm.can('panic')
        assert not fsm.can('calm')
        assert fsm.can('warn')

    def test_configured_transition_should_work(self, fsm):
        assert fsm.can('warn')

    def test_transition_should_change_state(self, fsm):
        fsm.addEvent('warn')
        assert fsm.getCurrentState() == 'yellow'

    def test_should_raise_exception_when_state_transition_is_not_allowed(self, fsm):
        pytest.raises(FSMError, fsm.addEvent, 'panic')
        pytest.raises(FSMError, fsm.addEvent, 'calm')
        pytest.raises(FSMError, fsm.addEvent, 'clear')

    def test_trigger_should_trigger_the_event_handler(self, fsm):
        assert fsm.getCurrentState() == "green"
        fsm.addEvent("warm")
        pytest.raises(FSMError, fsm.addEvent, 'unknown_event')
        assert fsm.getCurrentState() == "blue"

    def test_trigger_should_trigger_the_event_handler_with_args(self, fsm):
        assert fsm.getCurrentState() == "green"

        fsm.addEvent("warm", "any-positional-argument")
        assert fsm.getCurrentState() == "blue"
