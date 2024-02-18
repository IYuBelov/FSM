# coding=utf-8
#
# fysom - pYthOn Finite State Machine - this is a port of Jake
#         Gordon's javascript-state-machine to python
#         https://github.com/jakesgordon/javascript-state-machine
#
# Copyright (C) 2011 Mansour Behabadi <mansour@oxplot.com>, Jake Gordon
#                                        and other contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import unittest

from fsm.FSM import FysomError, Canceled, FysomGlobal, FysomGlobalMixin


class FysomGlobalTests(unittest.TestCase):

    def setUp(self):
        self.GSM = FysomGlobal(
            events=[('warn',  'green',  'yellow'),
                    {
                        'name': 'panic',
                        'src': ['green', 'yellow'],
                        'dst': 'red',
                        'cond': [  # can be function object or method name
                            'is_angry',  # by default target is "True"
                            {True: 'is_very_angry', 'else': 'yellow'}
                        ]
                    },
                    ('calm',  'red',    'yellow'),
                    ('clear', 'yellow', 'green')],
            initial='green',
            final='red',
            state_field='state'
        )

        class BaseModel(object):

            def __init__(self):
                self.state = None
                self.can_angry = True
                self.can_very_angry = False
                self.logs = []

            def is_angry(self, event):
                return self.can_angry

            def is_very_angry(self, event):
                return self.can_very_angry

            def on_change_state(self, event):
                self.logs.append('on_change_state')

            def check_true(self, event):
                return True

            def check_false(self, event):
                return False

        for _state in ('green', 'yellow', 'red'):
            for _at in ('enter', 'reenter', 'leave'):
                attr_name = 'on_%s_%s' % (_at, _state)

                def f(obj, event, attr_name=attr_name):
                    obj.logs.append(attr_name)

                setattr(BaseModel, attr_name, f)

        for _event in ('warn', 'panic', 'calm', 'clear'):
            for _at in ('before', 'after'):
                attr_name = 'on_%s_%s' % (_at, _event)

                def f(obj, event, attr_name=attr_name):
                    obj.logs.append(attr_name)

                setattr(BaseModel, attr_name, f)

        self.BaseModel = BaseModel

        class MixinModel(FysomGlobalMixin, BaseModel):

            GSM = self.GSM

        self.MixinModel = MixinModel

    def test_no_mixin_initial_state(self):
        obj = self.BaseModel()
        self.assertTrue(self.GSM.isstate(obj, 'none'))
        self.assertTrue(self.GSM.is_state(obj, 'none'))

    def test_mixin_initial_state(self):
        obj = self.MixinModel()
        self.assertTrue(obj.isstate('green'))
        self.assertTrue(obj.is_state('green'))

    def test_mixin_initial_event(self):
        obj = self.MixinModel()
        self.assertEqual(obj.logs, ['on_enter_green', 'on_change_state'])

    def test_mixin_current_property(self):
        obj = self.MixinModel()
        self.assertEqual(obj.current, 'green')
        obj.current = 'yellow'
        self.assertEqual(obj.current, 'yellow')

    def test_is_finished(self):
        obj = self.MixinModel()
        obj.can_very_angry = True
        obj.panic()
        self.assertTrue(obj.is_finished())

    def test_valid_transition_is_allowed(self):
        obj = self.MixinModel()
        self.assertTrue(obj.is_state('green'))
        obj.warn()
        self.assertTrue(obj.is_state('yellow'))

    def test_invalid_transition_is_not_allowed(self):
        obj = self.MixinModel()
        self.assertTrue(obj.is_state('green'))
        obj.can_very_angry = True
        obj.warn()
        self.assertTrue(obj.is_state('yellow'))
        obj.panic()
        self.assertTrue(obj.is_state('red'))
        self.assertRaises(FysomError, obj.clear)

    def tests_callbacks_order(self):
        obj = self.MixinModel()
        obj.logs = []
        obj.warn()
        self.assertEqual(obj.logs, ['on_before_warn', 'on_leave_green',
                                    'on_enter_yellow',
                                    'on_change_state', 'on_after_warn'])
        obj.can_angry = False
        obj.logs = []
        self.assertRaises(Canceled, obj.panic)
        self.assertEqual(obj.logs, [])
        self.assertTrue(obj.is_state('yellow'))
        obj.can_angry = True
        obj.can_very_angry = False
        obj.panic()
        self.assertEqual(obj.logs, ['on_before_panic', 'on_reenter_yellow',
                                    'on_after_panic'])

    def test_ok_condition_passed(self):
        obj = self.MixinModel()
        obj.can_very_angry = True
        obj.panic()
        self.assertTrue(obj.is_state('red'))

    def test_not_ok_condition_rejected(self):
        obj = self.MixinModel()
        obj.can_angry = False
        self.assertRaises(Canceled, obj.panic)
        self.assertTrue(obj.is_state('green'))

    def test_conditional_transition_passed(self):
        obj = self.MixinModel()
        self.assertTrue(obj.is_state('green'))
        obj.panic()
        self.assertFalse(obj.is_state('red'))
        self.assertTrue(obj.is_state('yellow'))

    def test_canceled_exception_with_event(self):
        obj = self.MixinModel()
        obj.can_angry = False
        self.assertRaises(Canceled, obj.panic)
        try:
            obj.panic()
        except Canceled as err:
            self.assertTrue(hasattr(err, 'event'))
            exc_event = err.event
            self.assertTrue(hasattr(exc_event, 'fsm'))
            self.assertTrue(hasattr(exc_event, 'obj'))
            self.assertTrue(hasattr(exc_event, 'src'))
            self.assertEqual(exc_event.src, 'green')
            self.assertTrue(hasattr(exc_event, 'dst'))
            self.assertEqual(exc_event.dst, 'red')
            self.assertTrue(hasattr(exc_event, 'args'))
            self.assertTrue(hasattr(exc_event, 'kwargs'))

    def test_trigger_works(self):
        obj = self.MixinModel()
        obj.trigger('warn')
        self.assertEqual(obj.current, 'yellow')
        self.assertRaises(FysomError, obj.trigger, 'unknown_event')
        self.assertEqual(obj.current, 'yellow')

    def test_no_state_field_specified(self):
        def _t():
            gsm = FysomGlobal(events=[])

        self.assertRaises(FysomError, _t)

    def test_cfg_parameter(self):
        gsm = FysomGlobal(
            cfg={
                'events': [
                    ('warn',  'green',  'yellow'),
                    {
                        'name': 'panic',
                        'src': ['green', 'yellow'],
                        'dst': 'red',
                        'cond': [  # can be function object or method name
                            'is_angry',  # by default target is "True"
                            {True: 'is_very_angry', 'else': 'yellow'}
                        ]
                    },
                    ('calm',  'red',    'yellow'),
                    ('clear', 'yellow', 'green')]},
            initial='green',
            final='red',
            state_field='state'
        )
        self.assertTrue(hasattr(gsm, 'warn'))
        self.assertTrue(hasattr(gsm, 'panic'))
        self.assertTrue(hasattr(gsm, 'calm'))
        self.assertTrue(hasattr(gsm, 'clear'))

    def test_manual_startup(self):
        gsm = FysomGlobal(
            events=[
                ('calm', 'red', 'yellow'),
                ('clear', 'yellow', 'green')],
            initial='red',
            state_field='state'
        )
        obj = self.BaseModel()
        self.assertTrue(gsm.is_state(obj, 'none'))
        self.assertTrue(hasattr(gsm, 'startup'))
        gsm.startup(obj)
        self.assertTrue(gsm.is_state(obj, 'red'))

    def test_manual_startup_event_name(self):
        gsm = FysomGlobal(
            events=[
                ('calm', 'red', 'yellow'),
                ('clear', 'yellow', 'green')],
            initial={'state': 'red', 'event': 'my_startup'},
            state_field='state'
        )
        obj = self.BaseModel()
        self.assertTrue(gsm.is_state(obj, 'none'))
        self.assertTrue(hasattr(gsm, 'my_startup'))
        gsm.my_startup(obj)
        self.assertTrue(gsm.current(obj) == 'red')

    def test_function_callback(self):
        def _func(event):
            event.obj.logs.append('function_callback')

        gsm = FysomGlobal(
            events=[
                ('calm', 'red', 'yellow'),
                ('clear', 'yellow', 'green')],
            callbacks={'on_after_clear': _func},
            initial='red',
            state_field='state'
        )
        obj = self.BaseModel()
        gsm.startup(obj)
        gsm.calm(obj)
        gsm.clear(obj)
        self.assertTrue('function_callback' in obj.logs)

    def test_asynchronous_transition(self):
        def _func(event):
            event.obj.logs.append('function_callback')

        def on_leave_red(event):
            return False

        gsm = FysomGlobal(
            events=[
                ('calm', 'red', 'yellow'),
                ('clear', 'yellow', 'green')],
            callbacks={'on_leave_red': on_leave_red, 'on_after_calm': _func},
            initial='red',
            state_field='state'
        )
        obj = self.BaseModel()
        gsm.startup(obj)
        self.assertTrue(gsm.is_state(obj, 'red'))
        gsm.calm(obj)
        self.assertTrue(gsm.is_state(obj, 'red'))
        self.assertTrue(hasattr(obj, 'transition'))
        self.assertFalse('functioon_callback' in obj.logs)
        obj.transition()
        self.assertTrue(gsm.is_state(obj, 'yellow'))
        self.assertFalse(hasattr(obj, 'transition'))
        self.assertTrue('function_callback' in obj.logs)

    def test_transition_with_args_kwargs(self):
        def _func(event):
            self.assertTrue(hasattr(event, 'args'))
            self.assertTrue(hasattr(event, 'kwargs'))
            self.assertTrue(hasattr(event, 'msg'))
            event.obj.logs.append('function_callback')

        gsm = FysomGlobal(
            events=[
                ('calm', 'red', 'yellow'),
                ('clear', 'yellow', 'green')],
            callbacks={'on_after_startup': _func},
            initial='red',
            state_field='state'
        )
        obj = self.BaseModel()
        gsm.startup(obj, msg='msg')
        self.assertTrue('function_callback' in obj.logs)

    def test_canceled_before_event_false(self):
        gsm = FysomGlobal(
            events=[
                ('calm', 'red', 'yellow'),
                ('clear', 'yellow', 'green')],
            callbacks={'on_before_calm': lambda e: False},
            initial='red',
            state_field='state'
        )
        obj = self.BaseModel()
        gsm.startup(obj)
        self.assertRaises(Canceled, gsm.calm, obj)

    def test_callable_or_basestring_condition(self):
        gsm = FysomGlobal(
            events=[
                {
                    'name': 'calm',
                    'src': 'red',
                    'dst': 'yellow',
                    'cond': lambda e: True,
                },
                {
                    'name': 'clear',
                    'src': 'yellow',
                    'dst': 'green',
                    'cond': 'check_false'
                }],
            initial='red',
            state_field='state'
        )
        obj = self.BaseModel()
        gsm.startup(obj)
        gsm.calm(obj)
        self.assertTrue(gsm.is_state(obj, 'yellow'))
        self.assertRaises(Canceled, gsm.clear, obj)
        self.assertTrue(gsm.is_state(obj, 'yellow'))

    def test_unknown_event(self):
        obj = self.MixinModel()
        self.assertFalse(obj.can('unknown_event'))
        self.assertTrue(self.GSM.cannot(obj, 'unknown_event'))

    def test_wildcard_src(self):
        gsm = FysomGlobal(
            events=[{'name': 'calm', 'dst': 'yellow'}],
            initial='red',
            state_field='state'
        )
        obj = self.BaseModel()
        gsm.startup(obj)
        self.assertTrue(gsm.is_state(obj, 'red'))
        gsm.calm(obj)
        self.assertTrue(gsm.is_state(obj, 'yellow'))
