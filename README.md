# Python Workers: FastMCP Example

This is an example of a Python Worker that uses the FastMCP package.

[![Deploy to Workers](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/danlapid/python-workers-mcp/)

>[!NOTE]
>Due to the [size](https://developers.cloudflare.com/workers/platform/limits/#worker-size) of the Worker, this example can only be deployed if you're using the Workers Paid plan. Free plan users will encounter deployment errors because this Worker exceeds the 3MB size limit.

## Developing and Deploying

To develop your Worker run:

```console
uv run pywrangler dev
```

To deploy your Worker run:

```console
uv run pywrangler deploy
```

## Testing

To test run:

```console
uv run pytest tests
```

## Linting and Formatting

This project uses Ruff for linting and formatting:

```console
uv ruff format . --check
uv ruff check .
```

## IDE Integration

To have good autocompletions in your IDE simply select .venv-workers/bin/python as your IDE's interpreter.
