import pytest
from fsm.FSM import FSM, FSMState, FSMConfigError


def config_case(testId, config, **kwargs):
    return pytest.param(config, id=testId, **kwargs)



class Prepare(FSMState):
    def enter(self, prevState, eventData):  # type: (FSMState, Any) -> None
        pass

    def leave(self, eventData):
        pass


class Fly(FSMState):
    def enter(self, prevState, eventData):  # type: (FSMState, Any) -> None
        pass

    def leave(self, eventData):
        pass


class PrepareAttack(FSMState):
    def enter(self, prevState, eventData):  # type: (FSMState, Any) -> None
        pass

    def leave(self, eventData):
        pass

    def reenter(self, eventData):
        print "REENTER", eventData


#

CONFIG = {
    "initial": {"state": "prepare"},
    "transitions": [
        {"src": "prepare", "dst": "fly", "event": "evFly"},
        {"src": ["fly", 'prepareAttack'], "dst": "prepareAttack", "event": "evPrepareAttack"},
        {"src": "*", "dst": "attack", "event": "evAttack"},
        {"src": "attack", "dst": "prepareFly", "event": "evPrepareFly"},
        {"src": "prepareFly", "dst": "fly", "event": "evFly"},
        {"src": "attack", "dst": "comeback", "event": "evComeback"},
        {"src": "comeback", "dst": "deactive", "event": "evDeactive"},
        {"src": "fly", "dst": "comeback", "event": "evComeback"}
    ],
    "states": [
        Prepare('prepare'),
        Fly('fly'),
        PrepareAttack('prepareAttack'),
    ],
}


def test_sfm_init():
    sfm = FSM(CONFIG)
    assert sfm.getCurrentState() == 'prepare'
    sfm.addEvent("evFly")
    assert sfm.getCurrentState() == 'fly'
    sfm.addEvent('evPrepareAttack')
    assert sfm.getCurrentState() == 'prepareAttack'
    sfm.addEvent('evPrepareAttack', {'Hellow': 1})
    assert sfm.getCurrentState() == 'prepareAttack'
    sfm.addEvent('evAttack')
    assert sfm.getCurrentState() == 'attack'


class IncorrectType(object):
    def __init__(self, name):
        self.__name = name


@pytest.mark.parametrize('config', [
    config_case(
        testId="without init have exception",
        config={
            "transitions": [
                {"src": "prepare", "dst": "fly", "event": "evFly"},
            ],
            "states": [
                Prepare('prepare'),
            ],
        }
    ),
    config_case(
        testId="without transition",
        config={
            "states": [
                Prepare('prepare'),
            ],
            "initial": {"state": "prepare"},
        }
    ),
    config_case(
        testId="Incorrect state type",
        config={
            "transitions": [
                {"src": "prepare", "dst": "fly", "event": "evFly"},
            ],
            "states": [
                IncorrectType('fake'),
            ],
            "initial": {"state": "ddd"},
        }
    ),
    config_case(
        testId="Final state '{}' doesn't have appropriate dst states",
        config={
            "transitions": [
                {"src": "prepare", "dst": "fly", "event": "evFly"},
            ],
            "states": [
                Prepare('prepare'),
            ],
            "initial": {"state": "some state"},
            "final": "IncorrectState",
        }
    ),
    config_case(
        testId="Final state doesn't have appropriate dst states",
        config={
            "transitions": [
                {"src": "prepare", "dst": "fly", "event": "evFly"},
            ],
            "states": [
                Prepare('prepare'),
            ],
            "initial": {"state": "some state"},
            "final": "IncorrectState",
        }
    ),
    config_case(
        testId="Final state '=' doesn't have appropriate dst states",
        config={
            "transitions": [
                {"src": "srcState", "dst": "=", "event": "evFly"},
            ],
            "states": [
                Prepare('prepare'),
            ],
            "initial": {"state": "some state"},
            "final": "IncorrectState",
        }
    ),
    config_case(
        testId="duplicated event",
        config={
            "transitions": [
                {"src": "srcState", "dst": "=", "event": "evFly"},
                {"src": "srcState2", "dst": "=", "event": "evFly"},
            ],
            "states": [
                Prepare('prepare'),
            ],
            "initial": {"state": "some state"},
            "final": "IncorrectState",
        }
    ),
    config_case(
        testId="duplicated initial event",
        config={
            "transitions": [
                {"src": "srcState", "dst": "=", "event": "evFly"},
            ],
            "states": [
                Prepare('prepare'),
            ],
            "initial": {"state": "some state", "event": "evFly"},
            "final": "IncorrectState",
        }
    ),
]
                         )
def test_sfm_init(config):
    with pytest.raises(FSMConfigError):
        FSM(config)
