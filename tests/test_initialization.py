# coding=utf-8


import unittest

from fsm.FSM import FSM


class TestFSMInitializationTests:

    def test_should_have_no_state_when_no_initial_state_is_given(self):
        fsm = FSM({
            'initial': {'state': 'none'},
            'transitions': [
                {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                {'event': 'clear', 'src': 'yellow', 'dst': 'green'}
            ]
        })
        assert fsm.getCurrentState() == 'none'

    def test_initial_state_should_be_green_when_configured(self):
        fsm = FSM({
            'initial': {'state': 'green'},
            'transitions': [
                {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                {'event': 'clear', 'src': 'yellow', 'dst': 'green'}
            ]
        })
        fsm.getCurrentState() == 'green'

    def test_initial_state_should_work_with_different_event_name(self):
        fsm = FSM({
            'initial': {'state': 'green', 'event': 'init'},
            'transitions': [
                {'event': 'panic', 'src': 'green', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'green'},
            ]
        })
        fsm.getCurrentState() == 'green'

    def test_deferred_initial_state_should_be_none_then_state(self):
        fsm = FSM({
            'initial': {'state': 'green', 'event': 'init'},
            'transitions': [
                {'event': 'panic', 'src': 'green', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'green'},
            ]
        })
        fsm.getCurrentState() == 'none'
        fsm.addEvent('init')
        fsm.getCurrentState() == 'green'

    def test_tuples_as_trasition_spec(self):
        fsm = FSM({
            'initial': {'state':'green'},
            'transitions': [
                {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                {'event': 'clear', 'src': 'yellow', 'dst': 'green'},
            ]
        })
        fsm.addEvent('warn')
        fsm.addEvent('panic')
        fsm.getCurrentState() == 'red'
        fsm.addEvent('calm')
        fsm.addEvent('clear')
        fsm.getCurrentState() == 'green'
