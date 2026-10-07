"""Stateless Vercel adapter; no uploaded documents or project state written to disk."""
import json,os,sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs,urlparse
os.environ['SESSION_ONLY']='1'
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from server import process
class handler(BaseHTTPRequestHandler):
    def reply(self,obj,status=200):
        data=json.dumps(obj).encode()
        if len(data)>4200000:obj={'error':'Session is too large. Copy/download the draft and start a fresh session.'};data=json.dumps(obj).encode();status=413
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if self.action()=='state':self.reply({'project':None,'model':bool(os.environ.get('OPENAI_API_KEY')),'session_only':True,'max_upload_bytes':2800000})
        else:self.reply({'error':'Unknown route'},404)
    def action(self):return parse_qs(urlparse(self.path).query).get('action',[urlparse(self.path).path.rsplit('/',1)[-1]])[0]
    def do_POST(self):
        try:
            size=int(self.headers.get('Content-Length',0))
            if size<=0 or size>4200000:
                if 0<size<=8400000: self.rfile.read(size)
                self.reply({'error':'Request is too large for the session demo.'},413);return
            b=json.loads(self.rfile.read(size));self.reply(process(self.action(),b))
        except (ValueError,KeyError,TypeError) as e:self.reply({'error':str(e)},400)
        except Exception:self.reply({'error':'Processing failed. Your browser session is still available; retry the request.'},500)
