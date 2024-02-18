import json
from collections import deque
from functools import partial


class Event:
    def __call__(self, *args, **kwargs):
        pass
    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def claer(self):
        pass


class Tokens:
    INIT_STATE = 'init_state'
    TRANSITIONS = 'transitions'
    SOURCE_STATE = 'source'
    DEST_STATE = 'dest'
    TRIGGER = 'event'


class State(object):
    def __init__(self, sfm):
        self.__sfm = sfm

    def fini(self):
        self.__sfm = None

    def deactivate(self):
        pass

    def activate(self):
        pass
    def _addEvent(self, eventName):
        self.__sfm.addEvent(eventName)

class _FSMState(object):
    def __init__(self, sfm, params, overrideState=None):
        self.stateName = params['state']
        self.transitionsByEvent = {}
        stateClass = State if overrideState is None else overrideState
        self.userState = stateClass(sfm)
    def fini(self):
        self.stateName = None
        self.userState.fini()


class Sfm(object):

    def __init__(self, config):
        self.__states = None
        self.__currentState = None
        self.__isRunning = False
        self.__events = deque()
        self.evStateChanged = Event()

    def fini(self):
        self.evStateChanged.clear()
        self.__currentState = None
        for state in self.__states:
            state.fini()
        self.__events.clear()
        self.__isRunning = False

    @classmethod
    def makeFromJson(cls, json_file):
        with open(json_file, 'r') as file:
            config = json.load(file)
            return Sfm(config)

    def addEvent(self, event):
        self.__events.append(event)
        if self.__isRunning:
            return

        if self.__currentState is None:
            return

        self.__isRunning = True

        while len(self.__events):
            eventName = self.__events.popleft()
            destState = self.__currentState.transitionsByEvent.get(eventName)
            if destState:
                oldState = self.__currentState.stateName
                newState = destState.stateName
                self.__currentState.userState.deactivate()
                self.__currentState = destState
                self.__currentState.userState.activate()
                self.evStateChanged(oldState, newState)

        self.__isRunning = False

    def getCurrentStateName(self):
        pass


class Sfm1(object):
    def __init__(self, config):

        self.__stateMap = {}
        self.__states = []
        self.__transitions = {}
        self.__currentStateIndex = 0
        self.evStateChanged = Event()
        self.isDestroyed = False

    @classmethod
    def makeFromJson(cls, json_file):
        with open(json_file, 'r') as file:
            config = json.load(file)
            return Sfm(config)

    def init(self, defaultState, *states):
        """
        :param defaultState: default state of the state machine
        :param states: other states
        :type states: FiniteStateMachineState
        """
        self.addState(defaultState)
        for state in states:
            self.addState(state)
        self.currentState().activate()

        self.evStateChanged = Event()
        self.isDestroyed = False

    def addEvent(self, eventName):

        pass

    def currentState(self):
        """
        :rtype: FiniteStateMachineState
        """
        return self.__states[self.__currentStateIndex]

    def currentStateIndex(self):
        """
        :rtype: int
        """
        return self.__currentStateIndex

    def getStateById(self, stateId):
        return self.__stateMap.get(stateId)

    def addState(self, newState):
        """
        :type newState: FiniteStateMachineState
        """
        assert newState not in self.__states
        self.__states.append(newState)

        stateId = newState.stateId
        if stateId != _UNINITIALIZED_STATE_ID:
            assert stateId not in self.__stateMap, "State id %s is already present in the state machine" % stateId
            self.__stateMap[stateId] = newState

    def addTransition(self, fromState, condition, toState, callback=None):
        """
        :type fromState: FiniteStateMachineState
        :type condition: (*args) -> bool
        :type toState: FiniteStateMachineState
        :type callback: callable
        """
        assert (fromState in self.__states) and (toState in self.__states) and (fromState != toState)
        transitions = self.__transitions.setdefault(self.__states.index(fromState), {})
        transitions[self.__states.index(toState)] = (condition, callback)

    def addTransitionById(self, fromStateId, condition, toStateId, callback=None):
        assert fromStateId in self.__stateMap and toStateId in self.__stateMap, "Both states have to be present in fsm in order for transition to be added, 1st state id: %d (isPresent: %s), 2nd state id: %d (isPresent: %s)" % (
        fromStateId, fromStateId in self.__stateMap, toStateId, toStateId in self.__stateMap)
        self.addTransition(self.__stateMap[fromStateId], condition, self.__stateMap[toStateId], callback)

    def addCallback(self, fromState, toState, callback):
        """
        :param fromState: FiniteStateMachineState
        :param toState: FiniteStateMachineState
        :param callback: callable
        """
        fromStateIndex = self.__states.index(fromState)
        assert fromStateIndex in self.__transitions, "State (index: %d, id: %s) does not have any transitions" % (
        fromStateIndex, fromState.stateId)

        toStateIndex = self.__states.index(toState)
        transitions = self.__transitions[fromStateIndex]
        assert toStateIndex in transitions, "Transition between states %d (id: %s) and %d (id: %s) is not available" % (

            fromStateIndex, fromState.stateId, toStateIndex, toState.stateId)
        transitions[toStateIndex] = (transitions[toStateIndex][0], callback)

    def addCallbackById(self, fromStateId, toStateId, callback):
        assert fromStateId in self.__stateMap and toStateId in self.__stateMap, "fromStateId: {}, toStateId: {}, Expected: {}".format(
            fromStateId, toStateId, self.__stateMap.keys())
        self.addCallback(self.__stateMap[fromStateId], self.__stateMap[toStateId], callback)

    def update(self, dt):
        transitionCount = 0
        while True:
            transited = self.updateTransitions()
            if not transited or self.isDestroyed:
                break

            transitionCount += 1
            if transitionCount > MAX_TRANSITIONS:
                LOG_ERROR("FiniteStateMachine",
                          "Finite state machine has exceeded the maximum amount of transitions per tick")
                break

        if not self.isDestroyed:
            self.currentState().update(dt)

    def updateTransitions(self):
        """
        Attempts to transit to the next state. Transition can only happen if the current state is ready for it and if
        conditions are satisfied for transition to another state. If conditions for multiple transitions are satisfied
        then state machine will transit to the first valid state it encounters in self.__transitions.

        :param args: arguments to condition checking method
        :return: True if transition was successful, False otherwise
        """
        if self.currentState().canTransit() and self.__currentStateIndex in self.__transitions:
            for toStateIndex, transition in self.__transitions[self.__currentStateIndex].iteritems():
                condition, callback = transition
                if condition is None or condition():
                    self.__performTransition(toStateIndex, callback)
                    return True
        return False

    def forceTransit(self, toState):
        """
        Direct order to state machine to transit to a specific state. Generally this method should NOT be used in the middle of
        finite state machine's owner update because the state of the object will change and the remaining part of the update might
        not be prepared for that. Interrupt() method is called instead of deactivate().

        :type toState: FiniteStateMachineState
        :rtype: bool
        """
        assert self.currentState() != toState, "Tried to transit to state we're currently in, stateId: %s" % self.currentState().stateId
        toStateIndex = self.__states.index(toState)

        transition = None
        if self.__currentStateIndex in self.__transitions:
            transition = self.__transitions[self.__currentStateIndex].get(toStateIndex)

        self.__performTransition(toStateIndex, transition[1] if transition else None, forced=True)

    def forceTransitById(self, toStateId):
        state = self.getStateById(toStateId)
        if not state:
            return False

        return self.forceTransit(state)

    def hasTransition(self, fromStateId, toStateId):
        fromStateIndex = self.__states.index(self.getStateById(fromStateId))
        toStateIndex = self.__states.index(self.getStateById(toStateId))
        return fromStateIndex in self.__transitions and toStateIndex in self.__transitions[fromStateIndex]

    def __performTransition(self, toStateIndex, callback, forced=False):
        previousState = self.currentState()
        if forced:
            self.currentState().interrupt()
        else:
            self.currentState().deactivate()

        self.__currentStateIndex = toStateIndex

        newState = self.currentState()
        newState.activate()

        if callback:
            callback()
        # state machine might have been destroyed during new state activation
        if not self.isDestroyed:
            self.evStateChanged(previousState, newState)

    def reset(self):
        self.currentState().interrupt()
        for state in self.__states:
            state.reset()
        self.__currentStateIndex = 0
        self.currentState().activate()

    def kill(self):
        self.isDestroyed = True
        self.evStateChanged = None

        for state in self.__states:
            state.kill()
        self.__states = None
        self.__stateMap.clear()
        self.__transitions.clear()
        self.__currentStateIndex = _UNINITIALIZED_STATE_ID


def f(name):
    print name

class A(object):
    def __init__(self):
        self.a = 1
    def __getattr__(self, item):
        print type(item)
        return partial(f, item)


a = A()

a.g()