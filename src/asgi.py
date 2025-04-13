from asyncio import Future, Event, Queue, ensure_future, sleep, create_task
from contextlib import contextmanager
from inspect import isawaitable
import typing

if typing.TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Literal,
        Optional,
        Protocol,
        TypedDict,
        Union,
        NotRequired,
    )
    from collections.abc import Awaitable, Iterable, MutableMapping

    class HTTPRequestEvent(TypedDict):
        type: Literal["http.request"]
        body: bytes
        more_body: bool

    class HTTPResponseDebugEvent(TypedDict):
        type: Literal["http.response.debug"]
        info: dict[str, object]

    class HTTPResponseStartEvent(TypedDict):
        type: Literal["http.response.start"]
        status: int
        headers: NotRequired[Iterable[tuple[bytes, bytes]]]
        trailers: NotRequired[bool]

    class HTTPResponseBodyEvent(TypedDict):
        type: Literal["http.response.body"]
        body: bytes
        more_body: NotRequired[bool]

    class HTTPResponseTrailersEvent(TypedDict):
        type: Literal["http.response.trailers"]
        headers: Iterable[tuple[bytes, bytes]]
        more_trailers: bool

    class HTTPServerPushEvent(TypedDict):
        type: Literal["http.response.push"]
        path: str
        headers: Iterable[tuple[bytes, bytes]]

    class HTTPDisconnectEvent(TypedDict):
        type: Literal["http.disconnect"]

    class WebSocketConnectEvent(TypedDict):
        type: Literal["websocket.connect"]

    class WebSocketAcceptEvent(TypedDict):
        type: Literal["websocket.accept"]
        subprotocol: NotRequired[str | None]
        headers: NotRequired[Iterable[tuple[bytes, bytes]]]

    class _WebSocketReceiveEventBytes(TypedDict):
        type: Literal["websocket.receive"]
        bytes: bytes
        text: NotRequired[None]

    class _WebSocketReceiveEventText(TypedDict):
        type: Literal["websocket.receive"]
        bytes: NotRequired[None]
        text: str

    WebSocketReceiveEvent = Union[
        _WebSocketReceiveEventBytes, _WebSocketReceiveEventText
    ]

    class _WebSocketSendEventBytes(TypedDict):
        type: Literal["websocket.send"]
        bytes: bytes
        text: NotRequired[None]

    class _WebSocketSendEventText(TypedDict):
        type: Literal["websocket.send"]
        bytes: NotRequired[None]
        text: str

    WebSocketSendEvent = Union[_WebSocketSendEventBytes, _WebSocketSendEventText]

    class WebSocketResponseStartEvent(TypedDict):
        type: Literal["websocket.http.response.start"]
        status: int
        headers: Iterable[tuple[bytes, bytes]]

    class WebSocketResponseBodyEvent(TypedDict):
        type: Literal["websocket.http.response.body"]
        body: bytes
        more_body: NotRequired[bool]

    class WebSocketDisconnectEvent(TypedDict):
        type: Literal["websocket.disconnect"]
        code: int
        reason: NotRequired[str | None]

    class WebSocketCloseEvent(TypedDict):
        type: Literal["websocket.close"]
        code: NotRequired[int]
        reason: NotRequired[str | None]

    class LifespanStartupEvent(TypedDict):
        type: Literal["lifespan.startup"]

    class LifespanShutdownEvent(TypedDict):
        type: Literal["lifespan.shutdown"]

    class LifespanStartupCompleteEvent(TypedDict):
        type: Literal["lifespan.startup.complete"]

    class LifespanStartupFailedEvent(TypedDict):
        type: Literal["lifespan.startup.failed"]
        message: str

    class LifespanShutdownCompleteEvent(TypedDict):
        type: Literal["lifespan.shutdown.complete"]

    class LifespanShutdownFailedEvent(TypedDict):
        type: Literal["lifespan.shutdown.failed"]
        message: str

    WebSocketEvent = Union[
        WebSocketReceiveEvent, WebSocketDisconnectEvent, WebSocketConnectEvent
    ]

    ASGIReceiveEvent = Union[
        HTTPRequestEvent,
        HTTPDisconnectEvent,
        WebSocketConnectEvent,
        WebSocketReceiveEvent,
        WebSocketDisconnectEvent,
        LifespanStartupEvent,
        LifespanShutdownEvent,
    ]

    ASGISendEvent = Union[
        HTTPResponseStartEvent,
        HTTPResponseBodyEvent,
        HTTPResponseTrailersEvent,
        HTTPServerPushEvent,
        HTTPDisconnectEvent,
        WebSocketAcceptEvent,
        WebSocketSendEvent,
        WebSocketResponseStartEvent,
        WebSocketResponseBodyEvent,
        WebSocketCloseEvent,
        LifespanStartupCompleteEvent,
        LifespanStartupFailedEvent,
        LifespanShutdownCompleteEvent,
        LifespanShutdownFailedEvent,
    ]


ASGI = {"spec_version": "2.0", "version": "3.0"}


background_tasks = set()


def run_in_background(coro):
    fut = ensure_future(coro)
    background_tasks.add(fut)
    fut.add_done_callback(background_tasks.discard)


@contextmanager
def acquire_js_buffer(pybuffer):
    from pyodide.ffi import create_proxy

    px = create_proxy(pybuffer)
    buf = px.getBuffer()
    px.destroy()
    try:
        yield buf.data
    finally:
        buf.release()


def request_to_scope(req, env, ws=False):
    from js import URL

    # @app.get("/example")
    # async def example(request: Request):
    #     request.headers.get("content-type")
    # - this will error if header is not "bytes" as in ASGI spec.
    headers = [(k.lower().encode(), v.encode()) for k, v in req.headers]
    url = URL.new(req.url)
    assert url.protocol[-1] == ":"
    scheme = url.protocol[:-1]
    path = url.pathname
    assert "?".startswith(url.search[0:1])
    query_string = url.search[1:].encode()
    if ws:
        ty = "websocket"
    else:
        ty = "http"
    return {
        "asgi": ASGI,
        "headers": headers,
        "http_version": "1.1",
        "method": req.method,
        "scheme": scheme,
        "path": path,
        "query_string": query_string,
        "type": ty,
        "env": env,
    }


async def start_application(app):
    shutdown_future = Future()

    async def shutdown():
        shutdown_future.set_result(None)
        await sleep(0)

    it = iter([{"type": "lifespan.startup"}, Future()])

    async def receive():
        res = next(it)
        if isawaitable(res):
            await res
        return res

    ready = Future()

    async def send(got):
        if got["type"] == "lifespan.startup.complete":
            ready.set_result(None)
            return
        if got["type"] == "lifespan.shutdown.complete":
            return
        raise RuntimeError(f"Unexpected lifespan event {got['type']}")

    run_in_background(
        app(
            {
                "asgi": ASGI,
                "state": {},
                "type": "lifespan",
            },
            receive,
            send,
        )
    )
    await ready
    return shutdown


async def process_request(app, req, env):
    from js import Object, Response, TransformStream
    from pyodide.ffi import create_proxy

    status = None
    headers = None
    result = Future()
    is_sse = False
    finished_response = Event()

    receive_queue = Queue()
    if req.body:
        async for data in req.body:
            await receive_queue.put(
                {
                    "body": data.to_bytes(),
                    "more_body": True,
                    "type": "http.request",
                }
            )
    await receive_queue.put({"body": b"", "more_body": False, "type": "http.request"})

    async def receive():
        message = None
        if not receive_queue.empty():
            message = await receive_queue.get()
        else:
            await finished_response.wait()
            message = {"type": "http.disconnect"}
        return message

    # Create a transform stream for handling streaming responses
    transform_stream = TransformStream.new()
    readable = transform_stream.readable
    writable = transform_stream.writable
    writer = writable.getWriter()

    async def send(got: "ASGISendEvent"):
        nonlocal status
        nonlocal headers
        nonlocal is_sse

        if got["type"] == "http.response.start":
            status = got["status"]
            # Like above, we need to convert byte-pairs into string explicitly.
            headers = [(k.decode(), v.decode()) for k, v in got["headers"]]
            # Check if this is a server-sent events response
            for k, v in headers:
                if k.lower() == "content-type" and v.lower().startswith(
                    "text/event-stream"
                ):
                    is_sse = True

                    # For SSE, create and return the response immediately after http.response.start
                    resp = Response.new(
                        readable, headers=Object.fromEntries(headers), status=status
                    )
                    result.set_result(resp)
                    break

        elif got["type"] == "http.response.body":
            body = got["body"]
            more_body = got.get("more_body", False)

            # Convert body to JS buffer
            px = create_proxy(body)
            buf = px.getBuffer()
            px.destroy()

            if is_sse:
                # For SSE, write chunk to the stream
                await writer.write(buf.data)
                # If this is the last chunk, close the writer
                if not more_body:
                    await writer.close()
                    finished_response.set()
            else:
                resp = Response.new(
                    buf.data, headers=Object.fromEntries(headers), status=status
                )
                result.set_result(resp)
                finished_response.set()

    # Run the application in the background to handle SSE
    async def run_app():
        try:
            await app(request_to_scope(req, env), receive, send)

            # If we get here and no response has been set yet, the app didn't generate a response
            if not result.done():
                await writer.close()  # Close the writer
                finished_response.set()
                result.set_exception(
                    RuntimeError("The application did not generate a response")
                )
        except Exception as e:
            # Handle any errors in the application
            if not result.done():
                await writer.close()  # Close the writer
                finished_response.set()
                result.set_exception(e)

    # Create task to run the application in the background
    app_task = create_task(run_app())

    # Wait for the result (the response)
    response = await result

    # For non-SSE responses, we need to wait for the application to complete
    if not is_sse:
        await app_task
    return response


async def process_websocket(app, req):
    from js import Response, WebSocketPair

    client, server = WebSocketPair.new().object_values()
    server.accept()
    queue = Queue()

    def onopen(evt):
        msg = {"type": "websocket.connect"}
        queue.put_nowait(msg)

    # onopen doesn't seem to get called. WS lifecycle events are a bit messed up
    # here.
    onopen(1)

    def onclose(evt):
        msg = {"type": "websocket.close", "code": evt.code, "reason": evt.reason}
        queue.put_nowait(msg)

    def onmessage(evt):
        msg = {"type": "websocket.receive", "text": evt.data}
        queue.put_nowait(msg)

    server.onopen = onopen
    server.onopen = onclose
    server.onmessage = onmessage

    async def ws_send(got):
        if got["type"] == "websocket.send":
            b = got.get("bytes", None)
            s = got.get("text", None)
            if b:
                with acquire_js_buffer(b) as jsbytes:
                    # Unlike the `Response` constructor,  server.send seems to
                    # eagerly copy the source buffer
                    server.send(jsbytes)
            if s:
                server.send(s)

        else:
            print(" == Not implemented", got["type"])

    async def ws_receive():
        received = await queue.get()
        return received

    env = {}
    run_in_background(app(request_to_scope(req, env, ws=True), ws_receive, ws_send))

    return Response.new(None, status=101, webSocket=client)


async def fetch(app, req, env):
    shutdown = await start_application(app)
    result = await process_request(app, req, env)
    await shutdown()
    return result


async def websocket(app, req):
    return await process_websocket(app, req)


def __getattr__(name):
    if name == "env":
        from fastapi import Depends, Request

        @Depends
        async def env(request: Request):
            return request.scope["env"]

        return env

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
