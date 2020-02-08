from __future__ import annotations

import attr


@attr.dataclass
class SameName:
    pass


@attr.dataclass
class Consumer:
    attribute: SameName

    def is_valid(self):
        return isinstance(self.attribute, SameName)
