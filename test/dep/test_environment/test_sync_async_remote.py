import asyncio
import ray
from typing import Callable, Any

ray.init()


# Example implementations
def sync_foo() -> str:
    return "sync result"


async def async_foo() -> str:
    await asyncio.sleep(1)  # Simulate async work
    return "async result"


@ray.remote
def remote_foo() -> str:
    return "remote result"


# Wrapper to make results awaitable
async def make_awaitable(func: Callable[..., Any], *args, **kwargs):
    if asyncio.iscoroutinefunction(func):
        # If the function is async, await it directly
        return await func(*args, **kwargs)
    elif hasattr(func, "remote"):
        # If the function is a Ray remote function, await its ObjectRef
        return await func.remote(*args, **kwargs)
    else:
        # For synchronous functions, wrap the result in an immediately resolved Future
        future = asyncio.Future()
        future.set_result(func(*args, **kwargs))
        return await future


# Example usage
async def main():
    # Call and await each version of foo
    sync_result = await make_awaitable(sync_foo)
    async_result = await make_awaitable(async_foo)
    remote_result = await make_awaitable(remote_foo)

    print(sync_result, async_result, remote_result)


asyncio.run(main())
