import asyncio
import http
import signal
import logging

import websockets


async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)


async def health_check(path, request_headers):
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"


async def main():
    # Set the stop condition when receiving SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with websockets.serve(
        echo,
        host="",
        port=8080,
        process_request=health_check,
    ):
        await stop


if __name__ == "__main__":
    logging.basicConfig(
       format="%(asctime)s %(message)s",
       level=logging.DEBUG,
    )
    print  ("Start websocket server ...")
    logging.debug("Logging started")

    asyncio.run(main())