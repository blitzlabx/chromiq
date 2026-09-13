from fastapi.testclient import TestClient
from app.main import app
from PIL import Image
import io

client=TestClient(app)
def test_health():
 assert client.get('/ping').status_code==200 and client.get('/health').json()['status']=='healthy'
def test_convert():
 r=client.post('/api/v1/convert',json={'color':{'value':'#ff0000'}}); assert r.status_code==200 and r.json()['formats']['rgb']=='rgb(255, 0, 0)'
def test_invalid(): assert client.post('/api/v1/convert',json={'color':{'value':'nope'}}).status_code==422
def test_contrast(): assert client.post('/api/v1/contrast',json={'foreground':{'value':'#fff'},'background':{'value':'#000'}}).json()['ratio']==21.0
def test_gradient(): assert client.post('/api/v1/gradient',json={'colors':['#000','#fff'],'stops':3}).status_code==200
def test_extract():
 im=Image.new('RGB',(20,20),(255,0,0)); b=io.BytesIO(); im.save(b,'PNG'); b.seek(0)
 r=client.post('/api/v1/extract',files={'file':('x.png',b,'image/png')}); assert r.status_code==200 and r.json()['colors'][0]['hex']=='#FF0000'
