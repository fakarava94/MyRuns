import asyncio
import http
import signal
import logging
import websockets
import os
from threading import Thread
from queue import Queue
import time

djangoWs = None
srvWs = None
clientReadQueue = None

async def processWs(queue):
    print('djangoWs: Running')
    global djangoWS
    while True:
        try:
            async with websockets.connect("ws://localhost:8081") as websocket:
                djangoWS = websocket
                print ("djangoWs: connect OK ", djangoWS)
                print ("djangoWs: connect OK ", queue)
                while True:
                    message = await websocket.recv()
                    print (" >>>> djangoWs::received: ", message)
                    queue.put(message)
                await asyncio.Future()
        except RuntimeError as e:
            time.sleep(5)

def djangoWsTask(queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.Future()
    asyncio.ensure_future(processWs(queue))
    try:
            loop.run_forever()
    finally:
            loop.close()

async def processQueue(queue):
    global djangoWS
    print('djangoQueue: Running')
    while True:
        # get a unit of work
        message = queue.get()
        # report
        print(f'>got {message}')
        await djangoWS.send(message)

def djangoQueueTask(queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.Future()
    asyncio.ensure_future(processQueue(queue))
    try:
            loop.run_forever()
    finally:
            loop.close()

async def processQueueSrv(queue):
    global srvWs
    print('srvConsumer: Running')
    while True:
        # get a unit of work
        message = queue.get()
        # report
        print(f'srvConsumer >got {message}')
        await srvWs.send(message)

def srvConsumer(queue):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.Future()
    asyncio.ensure_future(processQueueSrv(queue))
    try:
            loop.run_forever()
    finally:
            loop.close()

async def health_check(path, request_headers):
    if path == "/healthz":
        return http.HTTPStatus.OK, [], b"OK\n"

async def sendToDjango(websocket, queue):
    print("sendToDjango()")
    global clientReadQueue, srvWs
    srvWs = websocket
    async for message in websocket:
        clientReadQueue.put(message)


async def main(port, queue):
    print ("main, port=", port)
    async with websockets.serve(
        sendToDjango,
        host="",
        port=port,
    ) :
        await asyncio.Future()


if __name__ == "__main__":
    logging.basicConfig(
       format="%(asctime)s %(message)s",
       level=logging.INFO,
    )
    print  ("Start websocket server ...")
    logging.debug("Logging startted")
    port=os.environ.get('WSPORT', '8080')
    print('port=',port)
    global cientReadQueue
    
    # create the shared queues
    clientReadQueue = Queue()
    clientWriteQueue = Queue()
    # start the django thread ws client
    djangoClientWs = Thread(target=djangoWsTask, daemon=True, args=(clientWriteQueue,))
    djangoClientWs.start()
    print ("djangoClentWs=",djangoClientWs)
    # start the django thread queue consumer
    djangoClientQueue = Thread(target=djangoQueueTask, args=(clientReadQueue,))
    djangoClientQueue.start()
    print ("djangoClentQueue=",djangoClientQueue)
    
    # start server thread queue consumer
    srvConsumerTh = Thread(target=srvConsumer, args=(clientWriteQueue,))
    srvConsumerTh.start()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()
    asyncio.ensure_future(main(port, clientReadQueue))
    try:
            loop.run_forever()
    finally:
            loop.close()