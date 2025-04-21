# Python Workers: FastAPI-MCP Example

This is an example of a Model Context Protocol (MCP) Server that uses the [FastAPI-MCP package](https://github.com/tadata-org/fastapi_mcp), that you can deploy to Cloudflare. This example MCP server supports the [SSE remote transport](https://modelcontextprotocol.io/docs/concepts/transports#server-sent-events-sse). It does not handle authentication or authorization.

## Get Started

> [!NOTE]  
> [Python Workers](https://developers.cloudflare.com/workers/languages/python/) on Cloudflare are currently in beta. There are a few extra steps required to add external packages to your Worker, which will be simpler in the future.

1. `git clone https://github.com/danlapid/python-workers-mcp/`
2. Install Python3.12 and pip for Python 3.12. (*Currently, other versions of Python will not work - you must use 3.12*)
3. Then create a virtual environment and activate it from your shell:

```console
python3.12 -m venv .venv
source .venv/bin/activate
```

4. Within your virtual environment, install the pyodide CLI:

```console
.venv/bin/pip install pyodide-build
.venv/bin/pyodide venv .venv-pyodide
```

5. Download the vendored packages. For any additional packages, re-run this command.

```console
.venv-pyodide/bin/pip install -t src/vendor -r vendor.txt
```

### Developing and Deploying

To develop your Worker, run `npx wrangler@latest dev`.

To deploy your Worker, run `npx wrangler@latest deploy`.
