from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Tuple, List, Optional

from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructure
from pm4py.objects.process_tree.obj import ProcessTree

T = TypeVar('T', bound=IMDataStructure)


class FallThrough(ABC, Generic[T]):

    @classmethod
    @abstractmethod
    def holds(cls, t: T) -> bool:
        pass

    @classmethod
    @abstractmethod
    def apply(cls, t: T) -> Optional[Tuple[ProcessTree, List[T]]]:
        pass
