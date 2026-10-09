class FlyinParseError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class FlyinError(Exception):
    def __init__(self, *args):
        super().__init__(*args)