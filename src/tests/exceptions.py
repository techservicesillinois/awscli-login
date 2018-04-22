class NotRelativePathError(Exception):

    def __init__(self, path: str) -> None:
        mesg = 'Not a relative path: %s'
        super().__init__(mesg % path)
