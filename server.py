from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.mediastreams import MediaStreamTrack
from video import BnWTrack

logging.basicConfig()

logger = logging.Logger(name="info")


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

template = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def init(request:Request):
    return template.TemplateResponse("index.html", {"request":request})

@app.websocket('/ws')
async def websocket(websocket: WebSocket):
    await websocket.accept()
    logger.debug("started server")
    pc = RTCPeerConnection()
    
    @pc.on("datachannel")
    def on_datachannel(channel):
        print(f"channel {channel.label}")
        
        @channel.on("message")
        def send(message):
            print("message recu : ", message)
            channel.send(f"bien recu : {message}")
        
    @pc.on("icecandidate")
    async def ice_candidate(candidate: RTCIceCandidate):
        if candidate:
            print(f"\t\tcandidate ${candidate}")
            await websocket.send_json({
                "type" : "ice",
                "candidate": candidate
            })
            
    @pc.on("iceconnectionstatechange")
    def ic_nsc():
        print(f"etat de la connexion ICE : {pc.iceConnectionState}")
        
    @pc.on("connectionstatechange")
    def cschange():
        print(f"Etat de la connexion RTC : {pc.connectionState}")
        
    @pc.on("track")
    def on_track(track):
        print(f"track recu : {track.kind}")
        bw_track = BnWTrack(track)
        pc.addTrack(bw_track)
        
        @track.on("ended")
        def on_track_end():
            print("track fini")
            
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == 'offer':
                
                offre = RTCSessionDescription(data['sdp'], data['type'])
                
                await pc.setRemoteDescription(offre)
                
                reponse = await pc.createAnswer()
                await pc.setLocalDescription(reponse)
                
                await websocket.send_json({
                    "type" : pc.localDescription.type,
                    "sdp" : pc.localDescription.sdp
                })
                
            elif data["type"] == "ice":
                info = data["candidate"]["candidate"].split()
                candidate = RTCIceCandidate(
                    foundation=info[0],
                    ip=info[4],
                    port=info[5],
                    priority=info[2],
                    type=info[7],
                    component=info[1],
                    protocol=info[3],
                    sdpMid=data["candidate"]["sdpMid"],
                    sdpMLineIndex=data["candidate"]["sdpMLineIndex"]
                )
                await pc.addIceCandidate(candidate)
            
                
    except WebSocketDisconnect:
        logger.warning("disconnected")

if __name__ == '__main__':
    import uvicorn
    logger.debug("running the server")
    uvicorn.run("server:app", host="0.0.0.0", port=8002 ,reload=True)