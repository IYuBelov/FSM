# coding=utf-8

from fsm.FSM import FSM


class TestFysomSameDstTransitionTests:
    def test_if_src_not_specified_then_is_wildcard(self):
        fsm = FSM({
            'initial': {'state': 'hungry'},
            'transitions': [
                {'event': 'eat', 'src': 'hungry', 'dst': 'satisfied'},
                {'event': 'eat', 'src': 'satisfied', 'dst': 'full'},
                {'event': 'eat', 'src': 'full', 'dst': 'sick'},
                {'event': 'eat', 'src': 'sick', 'dst': '='},
                {'event': 'rest', 'src': '*', 'dst': 'hungry'},
                {'event': 'walk', 'src': '*', 'dst': '='},
                {'event': 'run', 'src': ['hungry', 'sick'], 'dst': '='},
                {'event': 'run', 'src': 'satisfied', 'dst': 'hungry'},
                {'event': 'run', 'src': 'full', 'dst': 'satisfied'}
            ]
        })
        fsm.addEvent('walk')
        assert fsm.getCurrentState() == 'hungry'
        fsm.addEvent('run')
        assert fsm.getCurrentState() == 'hungry'
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'satisfied'
        fsm.addEvent('walk')
        assert fsm.getCurrentState() == 'satisfied'
        fsm.addEvent('run')
        assert fsm.getCurrentState() == 'hungry'
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'satisfied'
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'full'
        fsm.addEvent('walk')
        assert fsm.getCurrentState() == 'full'
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'sick'
        fsm.addEvent('walk')
        assert fsm.getCurrentState() == 'sick'
        fsm.addEvent('run')
        assert fsm.getCurrentState() == 'sick'
        fsm.addEvent('rest')
        assert fsm.getCurrentState() == 'hungry'
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'satisfied'
        fsm.addEvent('run')
        assert fsm.getCurrentState() == 'hungry'
