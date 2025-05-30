# coding=utf-8


import unittest
import gc

from fsm.FSM import FSM


class TestFSMGarbageCollectionTests:

    def test_should_not_create_circular_ref(self):
        class MyTestObject(object):
            def __init__(self):
                self._states = []
                self._fsm = FSM({
                    'initial': {'state': 'green'},
                    'transitions': [
                        {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                        {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                        {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                        {'event': 'clear', 'src': 'yellow', 'dst': 'green'}
                    ]
                })

            def warn(self):
                self._fsm.addEvent('warn')

            def panic(self):
                self._fsm.addEvent('panic')

            def calm(self):
                self._fsm.addEvent('calm')

            def clear(self):
                self._fsm.addEvent('clear')

        obj = MyTestObject()
        obj.warn()
        obj.clear()
        del obj

        assert list(filter(lambda o: isinstance(o, MyTestObject), gc.get_objects())) == []

    def test_gc_should_not_break_callback(self):
        class MyTestObject(object):

            def __init__(self):
                self._fsm = None

            def warn(self):
                self._fsm.addEvent('warn')

            def panic(self):
                self._fsm.addEvent('panic')

            def calm(self):
                self._fsm.addEvent('calm')

            def clear(self):
                self._fsm.addEvent('clear')

        obj = MyTestObject()
        fsm = FSM({
            'initial': {'state': 'green'},
            'transitions': [
                {'event': 'warn', 'src': 'green', 'dst': 'yellow'},
                {'event': 'panic', 'src': 'yellow', 'dst': 'red'},
                {'event': 'calm', 'src': 'red', 'dst': 'yellow'},
                {'event': 'clear', 'src': 'yellow', 'dst': 'green'}
            ]
        })
        obj._fsm = fsm
        obj.warn()
        obj.clear()
        del obj
        fsm.addEvent('warn')
