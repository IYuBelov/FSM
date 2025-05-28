from typing import TypedDict, List, Union, Literal, Optional
from .FSM import FSMState



class Initial(TypedDict):
    state: str
    event: str


class Transition(TypedDict):
    src: Union[str, List[str], Literal["*"]]
    dst: str
    event: str


class Config(TypedDict):
    initial: Initial
    transitions: List[Transition]
    states: Optional[List[FSMState]]
