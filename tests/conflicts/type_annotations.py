import attr


@attr.s
class SameName:
    pass


@attr.dataclass
class Consumer:
    attribute: SameName

    def is_valid(self):
        return isinstance(self.attribute, SameName)
