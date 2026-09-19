from __future__ import annotations
import asyncio
from urllib.parse import parse_qs,urlsplit
from meylux.api import QuantitativeAPI

def _wire_response(status:int,content_type:str,body:bytes)->bytes:
    reason="OK" if status<400 else "ERROR"
    return (f"HTTP/1.1 {status} {reason}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Cache-Control: no-store\r\n"
            "Connection: close\r\n"
            "\r\n").encode()+body

async def serve_api(host:str,port:int,api:QuantitativeAPI)->None:
    async def handle(reader,writer):
        try:
            line=await reader.readline()
            if not line:return
            parts=line.decode("ascii","strict").strip().split(" ")
            if len(parts)!=3:
                response=await api.handle("BAD","/",{})
            else:
                method,target,_=parts
                parsed=urlsplit(target)
                query={k:v[-1] for k,v in parse_qs(parsed.query,keep_blank_values=True).items()}
                response=await api.handle(method,parsed.path,query)
            body=response.body.encode()
            writer.write(_wire_response(response.status,response.content_type,body))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
    server=await asyncio.start_server(handle,host,port)
    async with server:
        await server.serve_forever()
