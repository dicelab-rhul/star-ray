import asyncio
import ray
from typing import Union, Callable, Any


class _Future:
    def __init__(self, future: Union[asyncio.Future, ray.ObjectRef]):
        self._future = future

    @staticmethod
    def wrap(func: Callable[..., Any]):

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
    import time

    START = time.time()

    def sync_fun():
        time.sleep(1)
        return f"sync-result-{time.time() - START}"

    # Example usage
    async def async_func():
        await asyncio.sleep(1)
        return f"async-result-{time.time() - START}"

    @ray.remote
    def remote_func():
        time.sleep(1)
        return f"remote-result-{time.time() - START}"

    async def main():
        ray.init()
        future_sync = _Future.wrap(sync_fun)()
        future_async = _Future.wrap(async_func)()
        future_remote = _Future.wrap(remote_func)()

        print(await future_sync)
        print(await future_async)
        print(await future_remote)

    asyncio.run(main())
