from __future__ import annotations
import io, json, os, time
from collections import defaultdict
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image
from .color import *

BASE=Path(__file__).resolve().parent.parent
app=FastAPI(title='Chromiq API', version='1.0.0', description='Public color utility API by Blitz / blitzlabx')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

hits=defaultdict(list)
WINDOW=60; LIMIT=int(os.getenv('RATE_LIMIT','120'))
@app.middleware('http')
async def limiter(request:Request, call_next):
    ip=request.client.host if request.client else 'unknown'; now=time.time(); arr=[x for x in hits[ip] if x>now-WINDOW]; arr.append(now); hits[ip]=arr
    if len(arr)>LIMIT: raise HTTPException(429,'Rate limit exceeded. Try again shortly.')
    if request.headers.get('content-length') and int(request.headers['content-length'])>5_000_000: raise HTTPException(413,'Request too large.')
    return await call_next(request)

class ColorIn(BaseModel): value:str=Field(min_length=1,max_length=100); format:str='auto'
class ConvertIn(BaseModel): color:ColorIn; formats:list[str]=Field(default=['hex','rgb','rgba','hsl','hsla','hsv','hsb','cmyk'])
class PaletteIn(BaseModel): color:ColorIn; type:str='complementary'
class GradientIn(BaseModel): colors:list[str]=Field(min_length=2,max_length=12); stops:int=Field(default=8,ge=2,le=100); direction:str='to right'
class ContrastIn(BaseModel): foreground:ColorIn; background:ColorIn
class MixIn(BaseModel): first:ColorIn; second:ColorIn; amount:float=Field(default=.5,ge=0,le=1); space:str='rgb'
class AdjustIn(BaseModel): color:ColorIn; operation:str; amount:float=Field(ge=-1,le=1)

@app.get('/')
def home(): return FileResponse(BASE/'static/index.html')
@app.get('/ping')
def ping(): return {'status':'ok','service':'chromiq'}
@app.get('/health')
def health(): return {'status':'healthy','service':'chromiq','version':'1.0.0'}

def parsed(ci:ColorIn):
    try:return parse_color(ci.value,ci.format)
    except ValueError as e: raise HTTPException(422,str(e))

def serialize(c:Color): return to_dict(c)

@app.post('/api/v1/convert')
def convert(x:ConvertIn):
    d=serialize(parsed(x.color)); return {'input':x.color.model_dump(),'formats':{f:d[f] for f in x.formats if f in d},'color':d}
@app.post('/api/v1/palette')
def make_palette(x:PaletteIn):
    try: cols=palette(parsed(x.color),x.type.lower())
    except Exception as e: raise HTTPException(422,str(e))
    return {'type':x.type,'colors':[serialize(c) for c in cols]}
@app.post('/api/v1/gradient')
def gradient(x:GradientIn):
    try: cols=[parse_color(c) for c in x.colors]
    except ValueError as e: raise HTTPException(422,str(e))
    out=[]
    for i in range(x.stops):
        p=i/(x.stops-1); pos=p*(len(cols)-1); j=min(int(pos),len(cols)-2); t=pos-j; out.append(serialize(mix(cols[j],cols[j+1],t)))
    css=f'linear-gradient({x.direction}, '+', '.join(c['hex'] for c in out)+')'
    return {'direction':x.direction,'colors':out,'css':css}
@app.post('/api/v1/contrast')
def contrast_api(x:ContrastIn):
    ratio=contrast(parsed(x.foreground),parsed(x.background)); return {'ratio':round(ratio,4),'levels':accessibility(ratio),'foreground':serialize(parsed(x.foreground)),'background':serialize(parsed(x.background))}
@app.post('/api/v1/mix')
def mix_api(x:MixIn): return {'color':serialize(mix(parsed(x.first),parsed(x.second),x.amount,x.space))}
@app.post('/api/v1/adjust')
def adjust_api(x:AdjustIn):
    if x.operation not in {'hue','saturation','brightness','tint','shade','tone'}: raise HTTPException(422,'Unsupported adjustment operation.')
    return {'color':serialize(adjust(parsed(x.color),x.operation,x.amount))}
@app.post('/api/v1/random')
def random_color():
    import secrets
    c=Color(secrets.randbelow(256)/255,secrets.randbelow(256)/255,secrets.randbelow(256)/255); return {'color':serialize(c)}
@app.post('/api/v1/extract')
async def extract(file:UploadFile=File(...), count:int=8):
    if count<2 or count>20: raise HTTPException(422,'count must be 2-20')
    data=await file.read()
    if len(data)>5_000_000: raise HTTPException(413,'Image is too large (max 5 MB).')
    try:
        im=Image.open(io.BytesIO(data)).convert('RGB'); im.thumbnail((300,300))
        pal=im.quantize(colors=count, method=Image.Quantize.MEDIANCUT).convert('RGB')
        cols=pal.getcolors(pal.width*pal.height) or []
        vals=[]
        for _,(r,g,b) in sorted(cols,key=lambda x:x[0],reverse=True): vals.append(serialize(Color(r/255,g/255,b/255)))
        return {'colors':vals[:count]}
    except Exception as e: raise HTTPException(422,f'Unable to extract colors: {e}')
