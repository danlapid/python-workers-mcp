
from workers import DurableObject
from logger import logger
import sys
import httpx_patch  # noqa: F401
sys.path.insert(0, "/session/metadata/vendor")
sys.path.insert(0, "/session/metadata")


def setup_server(env):
    from fastapi import FastAPI, Request
    from pydantic import BaseModel
    from fastapi_mcp import FastApiMCP
    from exceptions import HTTPException, http_exception

    app = FastAPI()
    app.add_exception_handler(HTTPException, http_exception)

    mcp = FastApiMCP(app)

    # Mount the MCP server directly to your FastAPI app
    mcp.mount()
    # Auto-generated operation_id (something like "read_user_users__user_id__get")
    @app.get("/")
    async def root():
        return {"message": "Hello, World!"}

    @app.get("/env")
    async def root():
        return {"message": "Here is an example of getting an environment variable: " + env.MESSAGE}

    class Item(BaseModel):
        name: str
        description: str | None = None
        price: float
        tax: float | None = None

    @app.post("/items/")
    async def create_item(item: Item):
        return item

    @app.put("/items/{item_id}")
    async def create_item(item_id: int, item: Item, q: str | None = None):
        result = {"item_id": item_id, **item.dict()}
        if q:
            result.update({"q": q})
        return result

    @app.get("/items/{item_id}")
    async def read_item(item_id: int):
        return {"item_id": item_id}
    
    mcp.setup_server()
    return mcp, app


class FastMCPServer(DurableObject):
    def __init__(self, ctx, env):
        self.ctx = ctx
        self.env = env
        self.mcp, self.app = setup_server(self.env)

    async def call(self, request):
        import asgi
        return await asgi.fetch(self.app, request, self.env, self.ctx)

async def on_fetch(request, env):
    id = env.ns.idFromName("A")
    obj = env.ns.get(id)
    return await obj.call(request)
