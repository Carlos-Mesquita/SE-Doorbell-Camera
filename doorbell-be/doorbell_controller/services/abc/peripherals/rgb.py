from abc import ABC, abstractmethod

class IRGB(ABC):

    @abstractmethod
    def get_color(self):
        pass

    @abstractmethod
    def change_color(self, r: int, g: int, b: int):
        pass

    @abstractmethod
    def turn_on(self):
        pass

    @abstractmethod
    def turn_off(self):
        pass
