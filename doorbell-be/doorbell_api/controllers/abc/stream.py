from abc import ABC

class IStreamController(ABC):

    async def control_stream(self, start: bool):
        pass
