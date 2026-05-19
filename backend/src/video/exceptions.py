class ProjectNotFound(Exception):
    pass


class ProjectNotOwnedByUser(Exception):
    pass


class InvalidProjectStatus(Exception):
    def __init__(self, current: str, required: str):
        self.current = current
        self.required = required
        super().__init__(f"Project is {current!r}, expected {required!r}")


class GenerationNotFound(Exception):
    pass


class VideoGenerationFailed(Exception):
    pass
