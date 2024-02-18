import pytest
from fsm.FSM import FSM, FSMState


def case(testId, inputData, expectedResult, **kwargs):
    return pytest.param(inputData, expectedResult, id=testId, **kwargs)

class Prepare(FSMState):
    def enter(self, prevState, eventData):  # type: (FSMState, Any) -> None
        pass

    def fff(self):
        print("1")
        self.addEvent('evFly')
        print("end")

    def leave(self, eventData):
        pass


class Fly(FSMState):
    def enter(self, prevState, eventData):  # type: (FSMState, Any) -> None
        pass

    def leave(self, eventData):
        pass



STATES = [
    Prepare('prepare'),
    Fly('fly'),
]


CONFIG = {
    "initial": "prepare",
    "transitions": [
        {"src": "prepare", "dst": "fly", "event": "evFly"},
        {"src": "fly", "dst": "prepareAttack", "event": "evPrepareAttack"},
        {"src": "prepareAttack", "dst": "attack", "event": "evAttack"},
        {"src": "attack", "dst": "prepareFly", "event": "evPrepareFly"},
        {"src": "prepareFly", "dst": "fly", "event": "evFly"},
        {"src": "attack", "dst": "comeback", "event": "evComeback"},
        {"src": "comeback", "dst": "deactive", "event": "evDeactive"},
        {"src": "fly", "dst": "comeback", "event": "evComeback"}
    ]
}

# @pytest.mark.parametrize("inputData, expectedResult", [
#     case(
#         inputData={
#             "initial": "prepare",
#             "transitions": [
#                 {"src": "prepare", "dst": "fly", "event": "evFly"},
#                 {"src": "fly", "dst": "prepareAttack", "event": "evPrepareAttack"},
#                 {"src": "prepareAttack", "dst": "attack", "event": "evAttack"},
#                 {"src": "attack", "dst": "prepareFly", "event": "evPrepareFly"},
#                 {"src": "prepareFly", "dst": "fly", "event": "evFly"},
#                 {"src": "attack", "dst": "comeback", "event": "evComeback"},
#                 {"src": "comeback", "dst": "deactive", "event": "evDeactive"},
#                 {"src": "fly", "dst": "comeback", "event": "evComeback"}
#             ]},
#         expectedResult=
#     )
# ])


def test_sfm_init():

    sfm = FSM(CONFIG, STATES)

    assert sfm.getCurrentState() == 'prepare'

    #sfm.addEvent("evFly")

    assert sfm.getCurrentState() == 'fly'