# coding=utf-8

from fsm.FSM import FSM
from .test_many_to_many import TestFSMManyToManyTransitionTests


class TestFysomWildcardTransitionTests(TestFSMManyToManyTransitionTests):
    fsm_descr = {
        'initial': {'state': 'hungry'},
        'transitions': [
            {'event': 'eat', 'src': 'hungry', 'dst': 'satisfied'},
            {'event': 'eat', 'src': 'satisfied', 'dst': 'full'},
            {'event': 'eat', 'src': 'full', 'dst': 'sick'},
            {'event': 'rest', 'src': '*', 'dst': 'hungry'}
        ]
    }

    def test_if_src_not_specified_then_is_wildcard(self):
        fsm = FSM({
            'initial': {'state': 'hungry'},
            'transitions': [
                {'event': 'eat', 'src': 'hungry', 'dst': 'satisfied'},
                {'event': 'eat', 'src': 'satisfied', 'dst': 'full'},
                {'event': 'eat', 'src': 'full', 'dst': 'sick'},
                {'event': 'rest', 'dst': 'hungry'},
            ]
        })
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'satisfied'
        fsm.addEvent('rest')
        assert fsm.getCurrentState() == 'hungry'
        fsm.addEvent('eat')
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'full'
        fsm.addEvent('rest')
        assert fsm.getCurrentState() == 'hungry'
