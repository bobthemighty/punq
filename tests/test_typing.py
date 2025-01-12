from typing import assert_type

import punq as pq
from . import test_dependencies as d

container = pq.Container()

registration = pq._Registration(type[d.MessageWriter], pq.Scope.transient, d.TmpFileMessageWriter, pq.empty, [])
