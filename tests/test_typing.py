import typing as t

import punq as pq

from . import test_dependencies as d

container = pq.Container()

registration = pq._Registration(type[d.MessageWriter], pq.Scope.transient, d.TmpFileMessageWriter, pq.empty, [])


registration = pq._UntypedRegistration("My type", pq.Scope.transient, d.TmpFileMessageWriter, pq.empty, [])

t.assert_type(registration.builder, t.Callable[..., t.Any])
