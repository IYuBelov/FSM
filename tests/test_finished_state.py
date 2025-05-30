# coding=utf-8

import unittest
from fsm.FSM import FSM


class FSMFinishedStateTests(unittest.TestCase):
    def test_it_should_indicate_whether_fsm_in_finished_state(self):
        fsm = FSM({
            'initial': {'state': 'green'},
            'final': 'red',
            'transitions': [
                {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                {'event': 'clear', 'src': 'yellow', 'dst': 'green'}
            ]
        })
        assert not fsm.isFinished()
        fsm.addEvent('warn')
        assert not fsm.isFinished()
        fsm.addEvent('panic')
        assert fsm.isFinished()

    def test_never_finished_if_final_is_unspecified(self):
        fsm = FSM({
            'initial': {'state': 'green'},
            'transitions': [
                {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                {'event': 'clear', 'src': 'yellow', 'dst': 'green'}
            ]
        })
        assert not fsm.isFinished()
        fsm.addEvent('warn')
        assert not fsm.isFinished()
        fsm.addEvent('panic')
        assert not fsm.isFinished()
