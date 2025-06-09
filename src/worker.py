import sys

sys.path.insert(0, "/session/metadata/vendor")
sys.path.insert(0, "/session/metadata")


def setup_server():
    from mcp.server.fastmcp import FastMCP
    from starlette.middleware.cors import CORSMiddleware

    from exceptions import HTTPException, http_exception

    mcp = FastMCP("Demo", stateless_http=True)

    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    @mcp.resource("greeting://{name}")
    def get_greeting(name: str) -> str:
        """Get a personalized greeting"""
        return f"Hello, {name}!"

    @mcp.tool()
    def calculate_bmi(weight_kg: float, height_m: float) -> float:
        """Calculate BMI given weight in kg and height in meters"""
        return weight_kg / (height_m**2)

    @mcp.prompt()
    def echo_prompt(message: str) -> str:
        """Create an echo prompt"""
        return f"Please process this message: {message}"

    app = mcp.streamable_http_app()
    app.add_exception_handler(HTTPException, http_exception)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    return mcp, app


async def on_fetch(request, env, ctx):
    mcp, app = setup_server()
    import asgi

    return await asgi.fetch(app, request, env, ctx)
