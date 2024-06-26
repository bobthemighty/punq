from enum import Enum
from typing import Annotated, Generic, Type, TypeVar

import punq
from punq import PunqAnnotation

container = punq.Container()

class Topics(Enum):
    distance = '/distance'

T = TypeVar('T')

class Subscriber(Generic[T]):
    def __init__(self, msg_type: Type[T], topic: str):
        self.msg_type = msg_type
        self.topic = topic

class Test:
    def __init__(
        self,
        temp_sub: Annotated[Subscriber[float], PunqAnnotation, '/topic/temp'],
        dist_sub: Annotated[Subscriber[float], PunqAnnotation, Topics.distance],
        param1: Annotated[int, 'an annotation that is not for punq'],
    ):
        self.temp_sub: Subscriber[float] = temp_sub
        self.dist_sub: Subscriber[float] = dist_sub
        self.param1 = param1

def test_annotated_types():
    temp_sub = Subscriber(float, '/topic/temp')
    container.register(Annotated[Subscriber[float], PunqAnnotation, '/topic/temp'], instance=temp_sub)

    dist_sub = Subscriber(float, '/topic/dist')
    container.register(Annotated[Subscriber[float], PunqAnnotation, Topics.distance], instance=dist_sub)

    container.register(int, instance=88)

    container.register(Test)
    test: Test = container.resolve(Test)

    assert test.temp_sub.topic == '/topic/temp'

    assert test.dist_sub.topic == '/topic/dist'
    assert test.param1 == 88


test_annotated_types()