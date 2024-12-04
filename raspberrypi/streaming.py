import io
import logging
import socketserver
from http import server
from threading import Condition

### MPEG Streaming Server ###

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()
    
    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
        ## put camera's frame data inside buffer

class StreamingHandler(server.BaseHTTPRequestHandler):
    PAGE = """\
    <html>
    <head>
    <title> picam2 mjpeg streaming demo</title>
    </head>
    <body>
    <h1> Front Camera Streaming </h1>
    <img src="stream.mjpg" width="auto" height="auto" />
    </body>
    </html>
    """

    def do_get(self):
        global output
        if self.path == '/':
            self.send_response(301)