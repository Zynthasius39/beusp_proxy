import asyncio
import json
import logging
import sys
import time
from threading import Event, Thread
from typing import Optional

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout

from ..config import REQUEST_TIMEOUT


class HTTPClient:
    """HTTPClient base class.
    Running tasks in seperate worker thread,
    wrapping aiohttp methods.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[ClientTimeout] = ClientTimeout(REQUEST_TIMEOUT),
        *,
        ssl=True,
        loop=None,
        proxy=None,
        **kwargs
    ):
        # pylint: disable=R0913
        self._loop = asyncio.new_event_loop() if not loop else loop
        self._proxy = proxy
        self._ssl = ssl

        def _client_worker():
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._shevent = Event()
        self._thread = Thread(
            name=__name__, target=_client_worker, daemon=True)
        self._thread.start()
        self._session = ClientSession(
            base_url, loop=self._loop, timeout=timeout, **kwargs
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        """Stop the loop and close ClientSession"""

        # Disabled
        # Causes burying of uWSGI, Gunicorn server workers to hang
        # ClientSession keeps hanging

        async def close_session():
            await self._session.close()

        self.submit_coro(close_session)
        time.sleep(1)

        # Causes: RuntimeError: Cannot close a running event loop
        # self._loop.call_soon_threadsafe(self._loop.stop)

        # self._loop.call_soon_threadsafe(self._loop.close)

    def request(self, method, url, *, allow_redirects=True, **kwargs):
        """Blocking ClientSession.request wrapper.
        Submits and waits for the request.

        Reference:
        https://docs.aiohttp.org/en/stable/client_reference.html#ClientSession.request

        Returns:
            ClientResponse: Response object
        """
        try:
            res = self.submit_coro(
                self.request_coro,
                method,
                url,
                allow_redirects=allow_redirects,
                **kwargs
            ).result()
        except TimeoutError as e:
            logging.getLogger(__name__).error(e)
            raise HTTPClientError(e) from e
        except ClientError as e:
            logging.getLogger(__name__).error(e)
            sys.exit(1)

        return res

    def cr_read(self, cr: ClientResponse):
        """Read response's body as bytes
        by submitting it as a coroutine.

        Args:
            cr (ClientResponse): Response object

        Returns:
            dict: Response JSON
        """
        return self.submit_coro(cr.read).result()

    def cr_text(self, cr: ClientResponse, encoding=None):
        """Read response's body as text
        by submitting it as a coroutine.

        Args:
            cr (ClientResponse): Response object

        Returns:
            str: Response text
        """
        return self.submit_coro(cr.text, encoding=encoding).result()

    def cr_json(
        self,
        cr: ClientResponse,
        encoding=None,
        loads=json.loads,
        content_type="application/json",
    ):
        """Read response's body as JSON
        by submitting it as a coroutine.

        Args:
            cr (ClientResponse): Response object

        Returns:
            dict: Response JSON
        """
        return self.submit_coro(
            cr.json, encoding=encoding, loads=loads, content_type=content_type
        ).result()

    def gather(self, *args, return_exceptions=False):
        """asyncio.gather wrapper.

        Reference:
        https://docs.python.org/3/library/asyncio-task.html#asyncio.gather
        """

        async def _gather():
            return await asyncio.gather(*args, return_exceptions=return_exceptions)

        return self.submit_coro(_gather).result()

    def submit_coro(self, task, *args, **kargs):
        """Thread-safe method to submit coroutine task.

        Args:
            task (function): Coroutine

        Returns:
            Future: Future object
        """
        return asyncio.run_coroutine_threadsafe(task(*args, **kargs), self._loop)

    async def request_coro(self, method, url, *, allow_redirects=True, **kwargs):
        """ClientSession.request wrapper.

        Reference:
        https://docs.aiohttp.org/en/stable/client_reference.html#ClientSession.request

        Returns:
            coroutine: Wrapped coroutine
        """
        return await self._session.request(
            method,
            url,
            allow_redirects=allow_redirects,
            ssl=self._ssl,
            proxy=self._proxy,
            **kwargs
        )


class HTTPClientError(ClientError):
    """HTTPClient Error Base Exception"""
