import os
from aiohttp import web
import asyncio
import time


WS_FILE = os.path.join(os.path.dirname(__file__), "websocketNews.html")


async def wshandler(request: web.Request):
    resp = web.WebSocketResponse(heartbeat=5)
    available = resp.can_prepare(request)
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")

    await resp.prepare(request)
    await resp.send_str("Welcome!")

    try:
        print("Somebody joined.")
        for ws in request.app["sockets"]:
            await ws.send_str("Somebody joined")
        request.app["sockets"].append(resp)

        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                if msg.data == "in":
                    await resp.send_str("out")
                else:
                    for ws in request.app["sockets"]:
                        if ws is not resp:
                            await ws.send_str(msg.data)
            else:
                return resp
        return resp

    finally:
        request.app["sockets"].remove(resp)
        print("Somebody disconnected.")
        for ws in request.app["sockets"]:
            await ws.send_str("Somebody disconnected.")


async def on_shutdown(app: web.Application):
    for ws in app["sockets"]:
        await ws.close()


def init():
    app = web.Application()
    app["sockets"] = []
    app.router.add_get("/news", wshandler)
    app.on_shutdown.append(on_shutdown)
    return app


web.run_app(init())