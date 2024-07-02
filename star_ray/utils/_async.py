import asyncio
import ray
from typing import Union, Callable, Any, List


__all__ = ("_Future",)


class _Future:
    """
    A wrapper class that provides a unified interface for asyncio futures, tasks,
    and Ray object references. This class makes it easier to work with asynchronous
    and distributed computations in a consistent manner, abstracting away the differences
    between asyncio and Ray.
    """

    def __init__(self, future: Union[asyncio.Future, ray.ObjectRef]):
        super().__init__()
        self._future = future

    @staticmethod
    async def gather(futures: List["_Future"]):
        return await asyncio.gather(*(future.__await__() for future in futures))

    @staticmethod
    def call_sync(func: Callable[..., Any], *args, **kwargs):
        asyncio_future = asyncio.Future()
        try:
            result = func(*args, **kwargs)
            asyncio_future.set_result(result)
        except Exception as e:
            asyncio_future.set_exception(e)
        return _Future(asyncio_future)

    @staticmethod
    def call_async(func: Callable[..., Any], *args, **kwargs):
        # TODO we need to handle exceptions properly here...?
        return _Future(asyncio.create_task(func(*args, **kwargs)))

    @staticmethod
    def call_remote(func: Callable[..., Any], *args, **kwargs):
        return _Future(func.remote(*args, **kwargs))

    @staticmethod
    def wrap(func: Callable[..., Any]):
        """
        Wraps a given function to ensure that it returns an instance of _Future when called.
        This allows for a unified interface when working with async, sync, and Ray remote
        functions. The returned function, when called, will automatically wrap its result
        in a _Future object.

        Args:
            func (Callable[..., Any]): The function to wrap. This can be an asynchronous
                coroutine function, a synchronous function, or a Ray remote function.

        Returns:
            Callable[..., _Future]: A function that, when called, returns an instance of
            _Future wrapping the result of the original function call.

        Raises:
            TypeError: If the provided `func` argument is not callable.
        """
        if isinstance(func, ray.remote_function.RemoteFunction):

            def _wrap_remote_with_future(*args, **kwargs) -> "_Future":
                # Wrap the Ray object reference in _Future
                return _Future(func.remote(*args, **kwargs))

            return _wrap_remote_with_future

        elif asyncio.iscoroutinefunction(func):

            def _wrap_with_future(*args, **kwargs) -> "_Future":
                # Wrap the asyncio task in _Future
                return _Future(asyncio.create_task(func(*args, **kwargs)))

            return _wrap_with_future

        elif callable(func):

            def _wrap_sync_with_future(*args, **kwargs) -> "_Future":
                # Immediately resolve the result for a synchronous function
                asyncio_future = asyncio.Future()
                asyncio_future.set_result(func(*args, **kwargs))
                # Wrap the asyncio future in _Future
                return _Future(asyncio_future)

            return _wrap_sync_with_future
        else:
            raise TypeError(f"Failed to wrap: {func}, it is not callable.")

    def __await__(self):
        return (yield from self._future.__await__())


if __name__ == "__main__":
    # example usage

    from star_ray.agent import _Agent, Agent

    import time

    START = time.time()

    def sync_fun():
        time.sleep(1)
        return f"sync-result-{time.time() - START}"

    async def async_func():
        await asyncio.sleep(1)
        return f"async-result-{time.time() - START}"

    @ray.remote
    def remote_func():
        time.sleep(1)
        return f"remote-result-{time.time() - START}"

    class MyAgent(Agent):

        def __cycle__(self):
            print("cycle")

        def __execute(self, ambient):
            print("execute")

        def __sense__(self, ambient):
            print("sense")

    async def main():
        ray.init()

        agent = MyAgent([], [])

        # result = await _Future.call_sync(agent.__sense__, None) # this works...

        # result = await _Future.gather([_Future.call_sync(agent.__sense__, None)]) # this works...

        # agent = _Agent.new(agent)
        # result = await _Future.gather([agent.sense(None)])
        # print(result)

        # future_sync = _Future.wrap(sync_fun)()
        # future_async = _Future.wrap(async_func)()
        # future_remote = _Future.wrap(remote_func)()

        future_sync = _Future.call_sync(sync_fun)
        future_async = _Future.call_async(async_func)
        future_remote = _Future.call_remote(remote_func)
        futures = [future_sync, future_async, future_remote]
        results = await _Future.gather(futures)
        print(results)

    asyncio.run(main())
