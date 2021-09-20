import json

import anyio
from starlette.applications import Starlette
from starlette.responses import StreamingResponse
from starlette.routing import Route


async def number_generator():
    i = 0
    while True:
        yield 'event: number\n'
        yield f'data: {json.dumps({"number": i})}\n'
        yield '\n\n'
        i += 1
        await anyio.sleep(1)


async def sse(_):
    headers = {'cache-control': 'no-cache'}
    return StreamingResponse(number_generator(), headers=headers, media_type='text/event-stream')


app = Starlette(routes=[Route('/sse', sse)])
