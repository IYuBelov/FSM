# coding=utf-8

from __future__ import unicode_literals
import pytest
from fsm.FSM import FSM


class TestFysomUnicodeLiterals:
    def test_it_doesnt_break_with_unicode_literals(self):
        try:
            fsm = FSM({
                'initial': {'state': 'green'},
                'final': 'red',
                'transitions': [
                    {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                    {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                    {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                    {'event': 'clear', 'src': 'yellow', 'dst': 'green'},
                ]
            })
            assert True
        except Exception as e:
            pytest.fail("Unexpected exception raised: {}".format(e))

