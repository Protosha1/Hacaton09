# app/services/retry.py
"""
Retry helper for external API calls (LLM, TTS).
Retries only on transient errors: network issues, timeouts, 5xx.
Does NOT retry on 4xx - those are permanent.
"""
import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

import httpx


logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 10.0,
    label: str = "external call",
) -> T:
    """
    Call func() up to `attempts` times.
    Delay between attempts: base_delay * 2^(n-1), capped at max_delay.
    Raises the last exception if all attempts fail.
    """
    last_exc: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await func()
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ConnectError) as e:
            last_exc = e
            logger.warning(
                f"{label}: attempt {attempt}/{attempts} failed (network): {e}"
            )
        except httpx.HTTPStatusError as e:
            if 500 <= e.response.status_code < 600:
                last_exc = e
                logger.warning(
                    f"{label}: attempt {attempt}/{attempts} failed "
                    f"(HTTP {e.response.status_code})"
                )
            else:
                raise
        except Exception:
            raise

        if attempt < attempts:
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.info(f"{label}: retrying in {delay}s")
            await asyncio.sleep(delay)

    assert last_exc is not None
    logger.error(f"{label}: all {attempts} attempts failed")
    raise last_exc