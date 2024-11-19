from PIL.Image import Image

class Card():

    # base method to be overriden by stops and action cards
    def image(self, *args) -> Image:
        pass

    def __lt__(self, other: object) -> bool:
        from .stop import Stop
        from .action import Action
        from .special import Special
        # always do stop-action-special
        if isinstance(self, Stop):
            return True
        elif isinstance(self, Special):
            return False
        elif isinstance(self, Action) and isinstance(other, Special):
            return True
        elif isinstance(self, Action) and isinstance(other, Stop):
            return False
        else:
            return False