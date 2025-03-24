class InvalidEventPayload(Exception):
    def __init__(self, expected_fields: list[str]):
        self.fields = expected_fields
        super().__init__()

class ConfigException(Exception):
    def __init__(self, wrong_conf: str):
        super(f"Wrong configuration for {wrong_conf}! Check {wrong_conf}'s values in config/default.json!")

__all__ = [
    "InvalidEventPayload",
    "ConfigException"
]
