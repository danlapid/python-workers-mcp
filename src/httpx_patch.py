from httpx._transports.jsfetch import AsyncJavascriptFetchTransport

orig_handle_async_request = AsyncJavascriptFetchTransport.handle_async_request

async def handle_async_request(self, request):
    response = await orig_handle_async_request(self, request)
    # fix content-encoding headers because the javascript fetch handles that
    response.headers.update({"content-encoding": "identity"})
    return response

AsyncJavascriptFetchTransport.handle_async_request = handle_async_request