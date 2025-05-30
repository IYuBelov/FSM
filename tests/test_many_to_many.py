# coding=utf-8
import copy
from fsm.FSM import FSM

class TestFSMManyToManyTransitionTests:
    fsm_descr = {
        'initial': {"state": "hungry"},
        'transitions': [
            {'event': 'eat', 'src': 'hungry', 'dst': 'satisfied'},
            {'event': 'eat', 'src': 'satisfied', 'dst': 'full'},
            {'event': 'eat', 'src': 'full', 'dst': 'sick'},
            {'event': 'rest', 'src': ['hungry', 'satisfied', 'full', 'sick'], 'dst': 'hungry'}
        ]
    }

    def _get_descr(self, initial=None):
        mycopy = copy.deepcopy(self.fsm_descr)
        if initial:
            mycopy['initial'] = {'state': initial}
        return mycopy

    def test_rest_should_always_transition_to_hungry_state(self):
        fsm = FSM(self.fsm_descr)
        fsm.addEvent('rest')
        assert fsm.getCurrentState() == 'hungry'

        fsm = FSM(self._get_descr('satisfied'))
        fsm.addEvent('rest')
        assert fsm.getCurrentState() == 'hungry'

        fsm = FSM(self._get_descr('full'))
        fsm.addEvent('rest')
        assert fsm.getCurrentState() == 'hungry'

        fsm = FSM(self._get_descr('sick'))
        fsm.addEvent('rest')
        assert fsm.getCurrentState() == 'hungry'

    def test_eat_should_transition_to_satisfied_when_hungry(self):
        fsm = FSM(self._get_descr('hungry'))
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'satisfied'

    def test_eat_should_transition_to_full_when_satisfied(self):
        fsm = FSM(self._get_descr('satisfied'))
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'full'

    def test_eat_should_transition_to_sick_when_full(self):
        fsm = FSM(self._get_descr('full'))
        fsm.addEvent('eat')
        assert fsm.getCurrentState() == 'sick'
