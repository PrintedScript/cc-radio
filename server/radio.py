from aiohttp import web
import aiohttp
import requests
import ffmpeg
import asyncio
import base64
import threading

# connect to online radio with aac file format using requests
r = requests.get('https://radio.printedweb.me:8000/radio.mp3', stream=True)
chunk = ""
unprocessedchunks = []
audio = ffmpeg.input('pipe:0')
audio = ffmpeg.output(audio, 'pipe:1', format='dfpwm', ac=1, ar='48000')

try:
    print(f"""
    Connected to radio station
    Name: {r.headers["icy-name"]}
    Genre: {r.headers["icy-genre"]}
    Bitrate: {r.headers["icy-br"]}
    Description: {r.headers["icy-description"]}
    """)
except:
    pass

def addchunktoqueue():
    global unprocessedchunks
    while True:
        currentchunk = b""
        for chunk in r.iter_content(chunk_size=1000):
            if chunk:
                currentchunk = currentchunk + chunk
                if len(currentchunk) > 8000:
                    unprocessedchunks.append(currentchunk)
                    currentchunk = b""

def updateaudio():
    global chunk
    global unprocessedchunks
    while True:
        # get chunk from unprocessed chunks
        if len(unprocessedchunks) > 0:
            processingchunk = unprocessedchunks.pop(0)
            try:
                # convert mpeg audio to dfpwm format
                out, err = ffmpeg.run(audio, input=processingchunk, capture_stdout=True, capture_stderr=True)
                # send audio to client
                chunk = out #base64.b64encode(out).decode('utf-8')
            except ffmpeg.Error as e:
                if len(unprocessedchunks) > 0:
                    newchunk = unprocessedchunks.pop(0)
                    processingchunk = processingchunk + newchunk
                unprocessedchunks.insert(0, processingchunk)

async def stream(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    # remove socket from list when connection is closed
    while not ws.closed:
        currentchunk = chunk
        try:
            await ws.send_bytes(currentchunk)
        except:
            pass
        # wait for "chunk" variable to change
        await asyncio.sleep(0.1)
        while currentchunk == chunk:
            await asyncio.sleep(0.1)
    return ws


# run sendaudio function in a thread and start aiohttp server
if __name__ == '__main__':
    #loop = asyncio.get_event_loop()
    #loop.run_in_executor(None, sendaudio)
    threading.Thread(target=addchunktoqueue).start()
    threading.Thread(target=updateaudio).start()

    app = web.Application()
    app.router.add_get('/ws', stream)
    web.run_app(app)


