class FlyinParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class FlyinError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class FlyinUnreachableError(FlyinError):
    """The end zone cannot be reached from the start zone.

    Raised for a disconnected map (or one whose only route crosses a
    blocked zone) so the caller can tell "unsolvable" apart from a
    scheduling deadlock.
    """

    def __init__(self, *args):
        super().__init__(*args)
