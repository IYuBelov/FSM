from fsm.fsm import Sfm


def test_sfm_init():
    file = 'TestData/squadron.json'

    sfm = Sfm.makeFromJson(file)
    sfm.addEvent('evFly')

    assert sfm.getCurrentStateName() == 'fly'