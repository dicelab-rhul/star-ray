import asyncio
import logging
from typing import Any, List


class _EventBuffer(asyncio.Queue):
    """A custom asyncio.Queue for buffering events with a maximum size.

    Attributes:
        maxsize (int): The maximum size of the queue. Defaults to 0, indicating an infinite size.
    """

    async def put(self, item: Any):
        """Add an item to the queue, raising an error if the queue is full.

        Args:
            item (Any): The item to be added to the queue.

        Raises:
            IndexError: If attempting to add an item to a full queue.
        """
        if self.full():
            raise IndexError(f"Event buffer is full, failed to add item {item}.")
        await super().put(item)

    def get_all_nowait(self) -> List[Any]:
        """Retrieves all items from the buffer without blocking and empties the buffer.

        This method retrieves items synchronously and does not wait for items to become available,
        which may raise a [QueueEmpty] exception if the buffer is unexpectedly accessed asynchronously.

        Returns:
            List[Any]: A list of items retrieved from the buffer.
        """
        items = []
        while not self.empty():
            item = self.get_nowait()
            items.append(item)
            if len(items) >= self.maxsize:
                logging.getLogger("ray.serve").warning(
                    "returned early from event buffer `get_all`, the event buffer might be filling up to fast!",
                    stack_info=True,
                )
                return items
        return items
