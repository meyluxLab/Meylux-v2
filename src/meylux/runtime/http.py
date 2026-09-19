from __future__ import annotations
import asyncio
from urllib.parse import parse_qs,urlsplit
from meylux.api import QuantitativeAPI
async def serve_api(host:str,port:int,api:QuantitativeAPI)->None:
    async def handle(reader,writer):
        try:
            line=await reader.readline()
            if not line:return
            parts=line.decode("ascii","strict").strip().split(" ")
            if len(parts)!=3: response=await api.handle("BAD","/",{})
            else:
                method,target,_=parts; parsed=urlsplit(target); query={k:v[-1] for k,v in parse_qs(parsed.query,keep_blank_values=True).items()}; response=await api.handle(method,parsed.path,query)
            body=response.body.encode()
            writer.write((f"HTTP/1.1 {response.status} {'OK' if response.status<400 else 'ERROR'}\\r\\nContent-Type: {response.content_type}\\r\\nContent-Length: {len(body)}\\r\\nCache-Control: no-store\\r\\nConnection: close\\r\\n\\r\\n").encode()+body); await writer.drain()
        finally: writer.close(); await writer.wait_closed()
    server=await asyncio.start_server(handle,host,port)
    async with server: await server.serve_forever()
