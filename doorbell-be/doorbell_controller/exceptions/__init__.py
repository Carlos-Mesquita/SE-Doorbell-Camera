class ConfigException(Exception):
    def __init__(self, wrong_conf: str):
        super(f"Wrong configuration for {wrong_conf}! Check {wrong_conf}'s values in config/default.json!")

__all__ = [
    "ConfigException"
]
