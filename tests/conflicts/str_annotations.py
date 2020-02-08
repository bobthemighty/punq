import attr


@attr.s
class SameName:
    pass


@attr.dataclass
class Consumer:
    # Emulate "from __future__ import annotations"
    attribute: "SameName"

    def is_valid(self):
        return isinstance(self.attribute, SameName)
