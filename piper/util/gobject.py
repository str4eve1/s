from typing import Tuple

from gi.repository import GObject


def disconnect_handlers(obj: GObject.GObject, handlers: Tuple[int, ...]) -> None:
    """Disconnect supplied handlers from the supplied GObject."""

    def disconnect_non_zero(handler_id: int) -> None:
        if not handler_id > 0:
            return
        obj.disconnect(handler_id)

    for handler in handlers:
        disconnect_non_zero(handler)
