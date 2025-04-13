

from html_template import html_template
from exceptions import HTTPException, http_exception
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
class TextRequest(BaseModel):
    text: str

app = FastAPI(title="Text Reverser")

@app.get("/", response_class=HTMLResponse)
async def root():
    return html_template

@app.post("/reverse", response_class=JSONResponse)
async def reverse_text(request: TextRequest):
    reversed_text = request.text[::-1]
    return {"reversed_text": reversed_text}

# Starlette default http exception handler is sync which starlette tries to run in threadpool
# in https://github.com/encode/starlette/blob/master/starlette/_exception_handler.py#L61.
# Since we don't support threads we need to override it with the same function but async.
# TODO(now): change starlette's http_exception to be async, it is strictly slower to spawn a new
#            thread
app.add_exception_handler(HTTPException, http_exception)

async def on_fetch(request, env):
    import asgi
    return await asgi.fetch(app, request, env)