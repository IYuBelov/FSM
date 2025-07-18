import functools
import json
import os.path
import weakref
import types
import sys
from collections.abc import Callable
from typing import Dict, Any
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Type
    from FSM import Config

    PY3 = sys.version_info[0] >= 3

try:
    from collections.abc import Mapping
except ImportError:
    from collections import Mapping

__author__ = 'Igor Belov'
__copyright__ = 'Wargaming'
__credits__ = ['Mansour Behabadi', 'Jake Gordon']
__license__ = 'MIT'
__version__ = '${version}'
__maintainer__ = 'IYuBelov'
__email__ = 'IYuBelov@gmail.com'

_ALL_STATES = '*'
_SAME_DST = '='
_INIT_STATE = '__default_root_state'
_INIT_EVENT_NAME = '__default_root_setup_event'
_UPDATE_EVENT = '__update_event'
_MAX_TRANSITIONS = 100


class FSMError(Exception):
    pass


class FSMConfigError(Exception):
    pass


class FysomError(Exception):
    '''
        Raised whenever an unexpected event gets triggered.
        Optionally the event object can be attached to the exception
        in case of sharing event data.
    '''

    def __init__(self, msg, event=None):
        super(FysomError, self).__init__(msg)
        self.event = event


class Canceled(FysomError):
    '''
        Raised when an event is canceled due to the
        onbeforeevent handler returning False
    '''


def _weak_callback(func):
    '''
    Store a weak reference to a callback or method.
    '''
    if isinstance(func, types.MethodType):
        # Don't hold a reference to the object, otherwise we might create
        # a cycle.
        # Reference: http://stackoverflow.com/a/6975682
        # Tell coveralls to not cover this if block, as the Python 2.x case
        # doesn't test the 3.x code and vice versa.
        if sys.version_info[0] < 3:  # pragma: no cover
            # Python 2.x case
            obj_ref = weakref.ref(func.im_self)
            func_ref = weakref.ref(func.im_func)
        else:  # pragma: no cover
            # Python 3.x case
            obj_ref = weakref.ref(func.__self__)
            func_ref = weakref.ref(func.__func__)
        func = None

        def _callback(*args, **kwargs):
            obj = obj_ref()
            func = func_ref()
            if (obj is None) or (func is None):
                return
            return func(obj, *args, **kwargs)

        return _callback
    else:
        # We should be safe enough holding callback functions ourselves.
        return func


def _is_base_string(obj):  # pragma: no cover
    '''
        Returns if the object is an instance of basestring.
    '''
    try:
        return isinstance(obj, basestring)
    except NameError:
        return isinstance(obj, str)


class FSMState(object):
    def __init__(self, name):  # type: (str) -> None
        self.__name = name
        self.__fsm = None  # type: Optional[FSM]

    def __repr__(self):
        return 'State({!r}, {!r})'.format(self.name, self.__fsm)

    @property
    def name(self):
        return self.__name

    @property
    def fsm(self):
        return self.__fsm

    def sync(self, fsm):
        self.__fsm = weakref.proxy(fsm)

    def fini(self):
        pass

    def enter(self, prevState, eventData):  # type: (FSMState, Any) -> None
        pass

    def leave(self, eventData):
        pass

    def reenter(self, eventData):
        pass

    def interrupt(self, eventData):
        pass

    def canTransit(self):
        return True

    def update(self, dt):
        pass

    def addEvent(self, eventName, eventData=None):
        self.__fsm.addEvent(eventName, eventData)


class FSM(object):
    def __init__(self, cfg):  # type: (Config) -> None
        initial = cfg.get('initial')
        if initial is None:
            raise FSMConfigError("Config doesn't have 'initial' {}".format(cfg))
        initialState = initial['state']
        initialEvent = initial.get('event', _INIT_EVENT_NAME)

        transitions = cfg.get('transitions')
        if transitions is None:
            raise FSMConfigError("Config doesn't have 'transitions' {}".format(cfg))

        conditions = cfg.get('conditions', {})
        for condName, cond in conditions.items():
            if not callable(cond):
                raise FSMConfigError("Condition '{}' is not callable".format(condName))

        customStates = cfg.get('states', [])
        for state in customStates:
            if not isinstance(state, FSMState):
                raise FSMConfigError("State '{}' doesn't inherit FSMClass".format(state))
        customStatesMap = {state.name: state for state in customStates}

        statesMap = {_INIT_STATE: FSMState(_INIT_STATE), initialState: customStatesMap.get(initialState, FSMState(initialState)) }
        for transition in transitions:
            src = transition.get('src', _ALL_STATES)
            if _is_base_string(src):
                if src != _ALL_STATES:
                    if src not in statesMap:
                        statesMap[src] = customStatesMap.get(src, FSMState(src))
            else:
                for source in src:
                    if src == _ALL_STATES:
                        raise FSMConfigError('State * you can use only without another states')
                    if source not in statesMap:
                        statesMap[source] = customStatesMap.get(source, FSMState(source))

            dst = transition.get('dst')
            dst = src if dst == _SAME_DST else dst
            if dst != _ALL_STATES:
                dsts = [dst] if _is_base_string(dst) else dst
                for dst in dsts:
                    if dst not in statesMap:
                        statesMap[dst] = customStatesMap.get(dst, FSMState(dst))

        dsts = set()
        eventsCheck = {}
        conditionsForCheck = {}
        allActiveStates = [state for state in statesMap if state != _INIT_STATE]
        for transition in transitions:
            src = transition.get('src', _ALL_STATES)
            src = allActiveStates if src == _ALL_STATES else src
            srcs = [src] if _is_base_string(src) else src
            for src in srcs:
                dst = transition['dst']
                dsts.add(src if dst == _SAME_DST else dst)
                event = transition.get('event')
                if event:
                    eventSet = eventsCheck.get((src, dst), set())
                    if event in eventSet:
                        raise FSMConfigError("duplicated event {}".format(event))
                    eventSet.add(transition['event'])
                else:
                    conditionsSet = conditionsForCheck.get((src, dst), set())
                    conditionName = transition.get('condition')
                    condition = conditions.get(conditionName)
                    if condition is None:
                        raise FysomError("Condition '{}' doesn't exist".format(conditionName))
                    if condition in conditionsSet:
                        raise FysomError("Condition '{}' already exists".format(conditionName))
                    conditionsSet.add(condition)

        final = cfg.get('final', None)
        if final is not None:
            if final not in dsts:
                raise FSMConfigError("Final state '{}' doesn't have appropriate dst states".format(dsts))

        for state in statesMap.values():
            state.sync(self)

        transactionMap = {}
        eventTransitionMap = {}
        self.__addTransaction(statesMap[_INIT_STATE], statesMap[initialState], initialEvent, None, transactionMap, eventTransitionMap)
        for transition in transitions:
            src = transition.get('src', _ALL_STATES)
            src = allActiveStates if src == _ALL_STATES else src
            srcs = [src] if _is_base_string(src) else src
            dst = transition['dst']
            event = transition.get('event')
            for src in srcs:
                dstState = src if dst == _SAME_DST else dst
                conditionName = transition.get('condition')
                condition = conditions.get(conditionName)
                self.__addTransaction(statesMap[src], statesMap[dstState], event, condition, transactionMap, eventTransitionMap)

        self.__statesMap = statesMap  # type: Dict[str, FSMState]
        self.__transactionMap = transactionMap  # type: Dict[str, Dict[str, Tuple[str, Callable[[], bool]]]]
        self.__eventTransitionMap = eventTransitionMap  # type: Dict[str, Dict[str, Tuple[str, Callable[[], bool]]]]
        self.__currentStateId = _INIT_STATE  # type: str
        self.__final = final  # type: str
        self.__newEvents = []  # type: List[Tuple[str, Any]]
        self.__isRunning = False
        self.__isDestroyed = False
        self.__transitionsCount = 0
        self.__callbacks = {}

        isCustomInitialEvent = 'event' in initial
        if not isCustomInitialEvent:
            self.addEvent(_INIT_EVENT_NAME)

    @classmethod
    def makeSFMFromJSON(cls, json_file, states):  # type: (str, List[FSMState]) -> FSM
        if not os.path.exists(json_file):
            raise FSMConfigError("File '{}' doesn't exist".format(json_file))

        with open(json_file, 'r') as fd:
            cfg = json.load(fd)
            cfg['states'] = states
            return cls(cfg)

    def fini(self):
        for name in self.__statesMap:
            self.__statesMap[name].fini()
        self.__statesMap.clear()
        self.__transactionMap.clear()
        self.__callbacks.clear()
        del self.__newEvents[:]
        self.__isRunning = False
        self.__isDestroyed = True

    def addCallback(self, fromState, toState, callback):
        callbacks = self.__callbacks.get((fromState, toState), [])
        if callback not in callbacks:
            callbacks.append(callback)

    def removeCallback(self, fromState, toState, callback):
        callbacks = self.__callbacks.get((fromState, toState), [])
        if callback in callbacks:
            callbacks.remove(callback)

    def __callCallbacks(self, fromState, toState):
        callbacks = self.__callbacks.get((fromState, toState), [])
        for callback in callbacks:
            callback(fromState, toState)

    def addEvent(self, eventName, eventData=None):
        self.__newEvents.append((eventName, eventData))

        if self.__isRunning:
            return

        self.__isRunning = True
        try:
            self.__run()
        finally:
            self.__isRunning = False

    def can(self, event):
        '''
            Returns if the given event be fired in the current machine state.
        '''
        eventTransition = self.__eventTransitionMap.get(event)
        if not eventTransition:
            return False

        dst = eventTransition.get(self.__currentStateId)
        transition = self.__transactionMap.get(self.__currentStateId)
        return not self.isFinished() and transition and dst in transition

    def getCurrentState(self):
        return self.__currentStateId

    def isFinished(self):
        '''
            Returns if the state machine is in its final state.
        '''
        return self.__final and (self.__currentStateId == self.__final)

    def update(self, dt):  # type: (float) -> None
        transitionCount = 0
        while True:
            transited = self.__updateTransitions()
            if not transited or self.__isDestroyed:
                break

            transitionCount += 1
            if transitionCount > _MAX_TRANSITIONS:
                print("Finite state machine has exceeded the maximum amount of transitions per tick")
                break

        if not self.__isDestroyed:
            self.__currentState.update(dt)

    def __updateTransitions(self):
        """
        Attempts to transit to the next state. Transition can only happen if the current state is ready for it and if
        conditions are satisfied for transition to another state. If conditions for multiple transitions are satisfied
        then state machine will transit to the first valid state it encounters in self.__transitions.

        :param args: arguments to condition checking method
        :return: True if transition was successful, False otherwise
        """
        if not self.isFinished() and self.__currentState.canTransit() and self.__currentStateId in self.__transactionMap:
            for dst, info in self.__transactionMap[self.__currentStateId].items():
                event, condition = info
                if condition and condition():
                    self.__performTransition(dst, callback=None)
                    return True
        return False

    def __performTransition(self, dst, callback, forced=False):
        previousStateId = self.__currentStateId
        if forced:
            self.__currentState.interrupt({})
        else:
            self.__currentState.leave({})

        self.__currentStateId = dst
        self.__currentState.enter(self.__statesMap[previousStateId], {})

        if callback:
            callback()
        # state machine might have been destroyed during new state activation
        if not self.__isDestroyed:
            self.__callCallbacks(previousStateId, self.__currentStateId)

    @property
    def __currentState(self):
        return self.__statesMap[self.__currentStateId]

    def __addUpdateEvent(self):
        if self.__transitionsCount > _MAX_TRANSITIONS:
            print("Finite state machine has exceeded the maximum amount of transitions per tick")
            return

        self.addEvent(_UPDATE_EVENT)
        self.__transitionsCount += 1

    def __run(self):
        while self.__newEvents:
            events = list(self.__newEvents)
            del self.__newEvents[:]
            for eventName, eventData in events:
                self.__processEvent(eventName, eventData)

    def __processEvent(self, eventName, eventData):
        if eventData is None:
            eventData = {}

        if not self.can(eventName):
            raise FSMError("event {} inappropriate in current state {}".format(eventName, self.__currentStateId))

        # Finds the destination state, after this event is completed.
        dst = self.__eventTransitionMap[eventName][self.__currentStateId]
        info = self.__transactionMap[self.__currentStateId][dst]

        event, cond = info
        if cond is not None:
            if not cond():
                return

        if self.__currentStateId != dst:
            prevState = self.__statesMap[self.__currentStateId]
            prevState.leave(eventData)

            self.__currentStateId = dst
            currentState = self.__statesMap[self.__currentStateId]
            currentState.enter(prevState, eventData)

            self.__callCallbacks(prevState, currentState)
        else:
            currentState = self.__statesMap[self.__currentStateId]
            currentState.reenter(eventData)

    def __addTransaction(self, src, dst, event, condition, transactionMap, eventTransitionMap):
        transitions = transactionMap.setdefault(src.name, {})
        transitions[dst.name] = (event, condition)

        eventTransition = eventTransitionMap.setdefault(event, {})
        eventTransition[src.name] = dst.name


class Fysom(object):
    '''
        Wraps the complete finite state machine operations.
    '''

    def __init__(self, cfg=None, initial=None, events=None, callbacks=None,
                 final=None, **kwargs):
        '''
        Construct a Finite State Machine.

        Arguments:

            cfg         finite state machine specification,
                        a dictionary with keys 'initial', 'events', 'callbacks', 'final'

            initial     initial state

            events      a list of dictionaries (keys: 'name', 'src', 'dst')
                        or a list tuples (event name, source state or states,
                        destination state or states)

            callbacks   a dictionary mapping callback names to functions

            final       a state of the FSM where its is_finished() method returns True

        Named arguments override configuration dictionary.

        Example:

        >>> fsm = Fysom(events=[('tic', 'a', 'b'), ('toc', 'b', 'a')], initial='a')
        >>> fsm.current
        'a'
        >>> fsm.tic()
        >>> fsm.current
        'b'
        >>> fsm.toc()
        >>> fsm.current
        'a'

        '''
        if (sys.version_info[0] >= 3):
            super().__init__(**kwargs)

        cfg = {} if cfg is None else dict(cfg)
        # override cfg with named arguments
        if "events" not in cfg:
            cfg["events"] = []
        if "callbacks" not in cfg:
            cfg["callbacks"] = {}
        if initial:
            cfg["initial"] = initial
        if final:
            cfg["final"] = final
        if events:
            cfg["events"].extend(list(events))
        if callbacks:
            cfg["callbacks"].update(dict(callbacks))
        # convert 3-tuples in the event specification to dicts
        events_dicts = []
        for e in cfg["events"]:
            if isinstance(e, Mapping):
                events_dicts.append(e)
            elif hasattr(e, "__iter__"):
                name, src, dst = list(e)[:3]
                events_dicts.append({"name": name, "src": src, "dst": dst})
        cfg["events"] = events_dicts
        self.__apply(cfg)

    def isstate(self, state):
        '''
            Returns if the given state is the current state.
        '''
        return self.current == state

    is_state = isstate

    def can(self, event):
        '''
            Returns if the given event be fired in the current machine state.
        '''
        return (
                event in self.__map and
                ((self.current in self.__map[event]) or _ALL_STATES in self.__map[event]) and not
                hasattr(self, 'transition'))

    def cannot(self, event):
        '''
            Returns if the given event cannot be fired in the current state.
        '''
        return not self.can(event)

    def is_finished(self):
        '''
            Returns if the state machine is in its final state.
        '''
        return self.__final and (self.current == self.__final)

    def __apply(self, cfg):
        '''
            Does the heavy lifting of machine construction. More notably:
             >> Sets up the initial and finals states.
             >> Sets the event methods and callbacks into the same object namespace.
             >> Prepares the event to state transitions map.
        '''
        init = cfg['initial'] if 'initial' in cfg else None
        if self.__is_base_string(init):
            init = {'state': init}

        self.__final = cfg['final'] if 'final' in cfg else None

        events = cfg['events'] if 'events' in cfg else []
        callbacks = cfg['callbacks'] if 'callbacks' in cfg else {}
        tmap = {}
        self.__map = tmap

        def add(e):
            '''
                Adds the event into the machine map.
            '''
            if 'src' in e:
                src = [e['src']] if self.__is_base_string(
                    e['src']) else e['src']
            else:
                src = [_ALL_STATES]
            if e['name'] not in tmap:
                tmap[e['name']] = {}
            for s in src:
                tmap[e['name']][s] = e['dst']

        # Consider initial state as any other state that can have transition from none to
        # initial value on occurance of startup / init event ( if specified).
        if init:
            if 'event' not in init:
                init['event'] = 'startup'
            add({'name': init['event'], 'src': 'none', 'dst': init['state']})

        for e in events:
            add(e)

        # For all the events as present in machine map, construct the event
        # handler.
        for name in tmap:
            setattr(self, name, self.__build_event(name))

        # For all the callbacks, register them into the current object
        # namespace.
        for name in callbacks:
            setattr(self, name, _weak_callback(callbacks[name]))

        self.current = 'none'

        # If initialization need not be deferred, trigger the event for
        # transition to initial state.
        if init and 'defer' not in init:
            getattr(self, init['event'])()

    def __build_event(self, event):
        '''
            For every event in the state machine, prepares the event handler and
            registers the same into current object namespace.
        '''

        def fn(*args, **kwargs):

            if hasattr(self, 'transition'):
                raise FysomError(
                    "event %s inappropriate because previous transition did not complete" % event)

            # Check if this event can be triggered in the current state.
            if not self.can(event):
                raise FysomError(
                    "event %s inappropriate in current state %s" % (event, self.current))

            # On event occurence, source will always be the current state.
            src = self.current
            # Finds the destination state, after this event is completed.
            dst = ((src in self.__map[event] and self.__map[event][src]) or
                   _ALL_STATES in self.__map[event] and self.__map[event][_ALL_STATES])
            if dst == _SAME_DST:
                dst = src

            # Prepares the object with all the meta data to be passed to
            # callbacks.
            class _e_obj(object):
                pass

            e = _e_obj()
            e.fsm, e.event, e.src, e.dst = self, event, src, dst
            for k in kwargs:
                setattr(e, k, kwargs[k])

            setattr(e, 'args', args)

            # Try to trigger the before event, unless it gets canceled.
            if self.__before_event(e) is False:
                raise Canceled(
                    "Cannot trigger event {0} because the onbefore{0} handler returns False".format(e.event))

            # Wraps the activities that must constitute a single successful
            # transaction.
            if self.current != dst:
                def _tran():
                    delattr(self, 'transition')
                    self.current = dst
                    self.__enter_state(e)
                    self.__change_state(e)
                    self.__after_event(e)

                self.transition = _tran

                # Hook to perform asynchronous transition.
                if self.__leave_state(e) is not False:
                    self.transition()
            else:
                self.__reenter_state(e)
                self.__after_event(e)

        fn.__name__ = str(event)
        fn.__doc__ = ("Event handler for an {event} event. This event can be " +
                      "fired if the machine is in {states} states.".format(
                          event=event, states=self.__map[event].keys()))

        return fn

    def __before_event(self, e):
        '''
            Checks to see if the callback is registered before this event can be triggered.
        '''
        for fnname in ['onbefore' + e.event, 'on_before_' + e.event]:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def __after_event(self, e):
        '''
            Checks to see if the callback is registered for, after this event is completed.
        '''
        for fnname in ['onafter' + e.event, 'on' + e.event,
                       'on_after_' + e.event, 'on_' + e.event]:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def __leave_state(self, e):
        '''
            Checks to see if the machine can leave the current state and perform the transition.
            This is helpful if the asynchronous job needs to be completed before the machine can
            leave the current state.
        '''
        for fnname in ['onleave' + e.src, 'on_leave_' + e.src]:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def __enter_state(self, e):
        '''
            Executes the callback for onenter_state_ or on_state_.
        '''
        for fnname in ['onenter' + e.dst, 'on' + e.dst,
                       'on_enter_' + e.dst, 'on_' + e.dst]:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def __reenter_state(self, e):
        '''
            Executes the callback for onreenter_state_.
            This allows callbacks following reflexive transitions (i.e. where src == dst)
        '''
        for fnname in ['onreenter' + e.dst, 'on_reenter_' + e.dst]:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def __change_state(self, e):
        '''
            A general change state callback. This gets triggered at the time of state transition.
        '''
        for fnname in ['onchangestate', 'on_change_state']:
            if hasattr(self, fnname):
                return getattr(self, fnname)(e)

    def __is_base_string(self, object):  # pragma: no cover
        '''
            Returns if the object is an instance of basestring.
        '''
        try:
            return isinstance(object, basestring)
        except NameError:
            return isinstance(object, str)

    def trigger(self, event, *args, **kwargs):
        '''
            Triggers the given event.
            The event can be triggered by calling the event handler directly, for ex: fsm.eat()
            but this method will come in handy if the event is determined dynamically and you have
            the event name to trigger as a string.
        '''
        if not hasattr(self, event):
            raise FysomError(
                "There isn't any event registered as %s" % event)
        return getattr(self, event)(*args, **kwargs)


class FysomGlobalMixin(object):
    GSM = None  # global state machine instance, override this

    def __init__(self, *args, **kwargs):
        super(FysomGlobalMixin, self).__init__(*args, **kwargs)
        if self.is_state('none'):
            _initial = self.GSM._initial
            if _initial and not _initial.get('defer'):
                self.trigger(_initial['event'])

    def __getattribute__(self, attr):
        '''
            Proxy public event methods to global machine if available.
        '''
        try:
            return super(FysomGlobalMixin, self).__getattribute__(attr)
        except AttributeError as err:
            if not attr.startswith('_'):
                gsm_attr = getattr(self.GSM, attr)
                if callable(gsm_attr):
                    return functools.partial(gsm_attr, self)
            raise  # pragma: no cover

    @property
    def current(self):
        '''
            Simulate the behavior of Fysom's "current" attribute.
        '''
        return self.GSM.current(self)

    @current.setter
    def current(self, state):
        setattr(self, self.GSM.state_field, state)


class FysomGlobal(object):
    '''
        Target to be used as global machine.
    '''

    def __init__(self, cfg={}, initial=None, events=None, callbacks=None,
                 final=None, state_field=None, **kwargs):
        '''
        Construct a Global Finite State Machine.

        Takes same arguments as Fysom and an additional state_field
        to specify which field holds the state to be processed.

        Difference with Fysom:

        1.  Initial state will only be automatically triggered for class
            derived with FysomGlobalMixin.
        2.  Conditions and conditional transition are implemented.
        3.  When an event/transition is canceled, the event object will
            be attached to the raised Canceled exception. By doing this,
            additional information can be passed through the exception.

        Example:

        class Model(FysomGlobalMixin, object):
            GSM = FysomGlobal(
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

            def __init__(self):
                self.state = None
                super(Model, self).__init__()

            def is_angry(self, event):
                return True

            def is_very_angry(self, event):
                return False

        >>> obj = Model()
        >>> obj.current
        'green'
        >>> obj.warn()
        >>> obj.is_state('yellow')
        True
        >>> obj.panic()
        >>> obj.current
        'yellow'
        >>> obj.is_finished()
        False

        '''
        if sys.version_info[0] >= 3:
            super().__init__(**kwargs)
        cfg = dict(cfg)

        # state_field is required for global machine
        if not state_field:
            raise FysomError('state_field required for global machine')
        self.state_field = state_field

        if "events" not in cfg:
            cfg["events"] = []
        if "callbacks" not in cfg:
            cfg["callbacks"] = {}
        if initial:
            cfg['initial'] = initial
        if events:
            cfg["events"].extend(list(events))
        if callbacks:
            cfg["callbacks"].update(dict(callbacks))
        if final:
            cfg["final"] = final
        # convert 3-tuples in the event specification to dicts
        events_dicts = []
        for e in cfg["events"]:
            if isinstance(e, Mapping):
                events_dicts.append(e)
            elif hasattr(e, "__iter__"):
                name, src, dst = list(e)[:3]
                events_dicts.append({"name": name, "src": src, "dst": dst})
        cfg["events"] = events_dicts

        self._map = {}  # different with Fysom's _map attribute
        self._callbacks = {}
        self._initial = None
        self._final = None
        self._apply(cfg)

    def _apply(self, cfg):
        def add(e):
            if 'src' in e:
                src = [e['src']] if self._is_base_string(
                    e['src']) else e['src']
            else:
                src = [_ALL_STATES]

            _e = {'src': set(src), 'dst': e['dst']}
            conditions = e.get('cond')
            if conditions:
                _e['cond'] = _c = []
                if self._is_base_string(conditions) or callable(conditions):
                    _c.append({True: conditions})
                else:
                    for cond in conditions:
                        if self._is_base_string(cond):
                            _c.append({True: cond})
                        else:
                            _c.append(cond)
            self._map[e['name']] = _e

        initial = cfg['initial'] if 'initial' in cfg else None
        if self._is_base_string(initial):
            initial = {'state': initial}
        if initial:
            if 'event' not in initial:
                initial['event'] = 'startup'
            self._initial = initial
            add({'name': initial['event'],
                 'src': 'none', 'dst': initial['state']})

        if 'final' in cfg:
            self._final = cfg['final']

        for e in cfg['events']:
            add(e)

        for event in self._map:
            setattr(self, event, self._build_event(event))

        for name, callback in cfg['callbacks'].items():
            self._callbacks[name] = _weak_callback(callback)

    def _build_event(self, event):
        def fn(obj, *args, **kwargs):
            if not self.can(obj, event):
                raise FysomError(
                    'event %s inappropriate in current state %s'
                    % (event, self.current(obj)))

            # Prepare the event object with all the meta data to pas through.
            # On event occurrence, source will always be the current state.
            e = self._e_obj()
            e.fsm, e.obj, e.event, e.src, e.dst = (
                self, obj, event, self.current(obj), self._map[event]['dst'])
            setattr(e, 'args', args)
            setattr(e, 'kwargs', kwargs)
            for k, v in kwargs.items():
                setattr(e, k, v)

            # check conditions first, event dst may change during
            # checking conditions
            for c in self._map[event].get('cond', ()):
                target = True in c
                cond = c[target]
                _c_r = self._check_condition(obj, cond, target, e)
                if not _c_r:
                    if 'else' in c:
                        e.dst = c['else']
                        break
                    else:
                        raise Canceled(
                            'Cannot trigger event {0} because the {1} '
                            'condition not returns {2}'.format(
                                event, cond, target), e
                        )

            # try to trigger the before event, unless it gets cancelled.
            if self._before_event(obj, e) is False:
                raise Canceled(
                    'Cannot trigger event {0} because the onbefore{0} '
                    'handler returns False'.format(event), e)

            # wraps the activities that must constitute a single transaction
            if self.current(obj) != e.dst:
                def _trans():
                    delattr(obj, 'transition')
                    setattr(obj, self.state_field, e.dst)
                    self._enter_state(obj, e)
                    self._change_state(obj, e)
                    self._after_event(obj, e)

                obj.transition = _trans

                # Hook to perform asynchronous transition
                if self._leave_state(obj, e) is not False:
                    obj.transition()
            else:
                self._reenter_state(obj, e)
                self._after_event(obj, e)

        fn.__name__ = str(event)
        fn.__doc__ = (
            "Event handler for an {event} event. This event can be "
            "fired if the machine is in {states} states.".format(
                event=event, states=self._map[event]['src']))

        return fn

    class _e_obj(object):
        pass

    @staticmethod
    def _is_base_string(object):  # pragma: no cover
        try:
            return isinstance(object, basestring)  # noqa
        except NameError:
            return isinstance(object, str)  # noqa

    def _do_callbacks(self, obj, callbacks, *args, **kwargs):
        for cb in callbacks:
            if cb in self._callbacks:
                return self._callbacks[cb](*args, **kwargs)
            if hasattr(obj, cb):
                return getattr(obj, cb)(*args, **kwargs)

    def _check_condition(self, obj, func, target, e):
        if callable(func):
            return func(e) is target
        return self._do_callbacks(obj, [func], e) is target

    def _before_event(self, obj, e):
        callbacks = ['onbefore' + e.event, 'on_before_' + e.event]
        return self._do_callbacks(obj, callbacks, e)

    def _after_event(self, obj, e):
        callbacks = ['onafter' + e.event, 'on' + e.event,
                     'on_after_' + e.event, 'on_' + e.event]
        return self._do_callbacks(obj, callbacks, e)

    def _leave_state(self, obj, e):
        callbacks = ['onleave' + e.src, 'on_leave_' + e.src]
        return self._do_callbacks(obj, callbacks, e)

    def _enter_state(self, obj, e):
        callbacks = ['onenter' + e.dst, 'on' + e.dst,
                     'on_enter_' + e.dst, 'on_' + e.dst]
        return self._do_callbacks(obj, callbacks, e)

    def _reenter_state(self, obj, e):
        callbacks = ['onreenter' + e.dst, 'on_reenter_' + e.dst]
        return self._do_callbacks(obj, callbacks, e)

    def _change_state(self, obj, e):
        callbacks = ['onchangestate', 'on_change_state']
        return self._do_callbacks(obj, callbacks, e)

    def current(self, obj):
        return getattr(obj, self.state_field) or 'none'

    def isstate(self, obj, state):
        return self.current(obj) == state

    is_state = isstate

    def can(self, obj, event):
        if event not in self._map or hasattr(obj, 'transition'):
            return False
        src = self._map[event]['src']
        return self.current(obj) in src or _ALL_STATES in src

    def cannot(self, obj, event):
        return not self.can(obj, event)

    def is_finished(self, obj):
        return self._final and (self.current(obj) == self._final)

    def trigger(self, obj, event, *args, **kwargs):
        if not hasattr(self, event):
            raise FysomError(
                "There isn't any event registered as %s" % event)
        return getattr(self, event)(obj, *args, **kwargs)
