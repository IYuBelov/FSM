from typing import TypedDict, List, Union, Literal, Optional, Dict, Callable
from .FSM import FSMState



class Initial(TypedDict):
    state: str
    event: str


class Transition(TypedDict):
    src: Union[str, List[str], Literal["*"]]
    dst: str
    event: str
    condition: Optional[str]


class Config(TypedDict):
    initial: Initial
    transitions: List[Transition]
    states: Optional[List[FSMState]]
    conditions: Optional[Dict[str, Callable[[], bool]]]
