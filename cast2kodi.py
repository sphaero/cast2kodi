#!/usr/bin/python3
#
# cast2kody.py  Arnaud Loonstra <arnaud@sphaero.org>
#
# Cast2kody.py is a very simple script which runs a Gstreamer pipeline to
# capture the desktop and setup a tcpserver for the stream. It then sends
# a command to Kodi's API to open the TCP stream. This has been tested for
# low latency streaming. The experiences latency is caused by Kodi which
# probably buffers data a lot before playing. Experienced latencies are 
# beyond 5 seconds
#
# LICENSE: GPLv3, see gpl.org

import sys
import socket
import platform
if sys.version_info.major > 2:
    import subprocess
else:
    import commands as subprocess
import json
import requests, base64
import _thread as thread

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, GLib, Gst

# TIP: you can also use openh264enc instead of x264enc

#GST_PIPELINE = '( ximagesrc endx=1920 endy=1080 is-live=1 ! videoconvert ! x264enc bitrate=6000 bytestream=true ! rtph264pay name=pay0 pt=96 )'
#GST_PIPELINE = '( ximagesrc startx=1 starty=1 endx=1920 endy=1080 ! videoconvert ! x264enc bitrate=6000 threads=2 intra-refresh=true tune=zerolatency ! video/x-h264, profile=main ! rtph264pay name=pay0 pt=96 )'
#GST_PIPELINE = '( videotestsrc is-live=1 ! timeoverlay shaded-background=true font-desc="Sans, 24" ! x264enc ! video/x-h264, profile=main ! mpegtsmux ! rtpmp2tpay name=pay0 )'
if platform.system() == "Window":
    GST_PIPELINE = '( gdiscreencapsrc ! videoconvert ! video/x-raw,format=I420 !jpegenc ! rtpjpegpay name=pay0 )'
    GST_PIPELINE = '( gdiscreencapsrc ! videoconvert ! x264enc bitrate=6000 threads=2 intra-refresh=true tune=zerolatency ! rtph264pay name=pay0 pt=96 )'
elif platform.system() == "Darwin":
    GST_PIPELINE = '( avfvideosrc capture-screen-cursor=true capture-screen=true ! videoconvert ! video/x-raw,format=I420 !jpegenc ! rtpjpegpay name=pay0 )'
    
GST_PIPELINE_AUDIO = "( pulsesrc do-timestamp=true provide-clock=true buffer-time=20000 ! audio/x-raw,format=S16BE,channels=1,rate=22000 ! rtpL16pay max-ptime=20000000 name=pay0 )"

def get_pulse_device():
    return subprocess.run("pactl list | grep -A2 'Source #' | grep 'Name: .*\.monitor$' |  cut -d' ' -f2|head -1", \
        shell=True, stdout=subprocess.PIPE, universal_newlines=True)

def get_local_ip():
    """ 
    Ugly but it works, better go through the routing table
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def cast_to_kodi(kodi_url, localip):
    usrPass = b"user_name:password"
    b64Val = base64.b64encode(usrPass)
    url = kodi_url + '/jsonrpc'
    payload = {"jsonrpc":"2.0", "id":1, "method": "Player.Open", "params":{"item":{"file":"tcp://"+localip+":4321"}}}
    r=requests.post(url, 
                headers={"Authorization": "Basic %s" % b64Val,'content-type': 'application/json'},
                data=json.dumps(payload))

def on_message(bus, message, loop):
    mtype = message.type
    """
        Gstreamer Message Types and how to parse
        https://lazka.github.io/pgi-docs/Gst-1.0/flags.html#Gst.MessageType
    """ 
 
    if mtype == Gst.MessageType.EOS:
        # Handle End of Stream
        print("End of stream")
    elif mtype == Gst.MessageType.ERROR:
        # Handle Errors
        err, debug = message.parse_error() 
        print(err, debug)
    elif mtype == Gst.MessageType.WARNING:
        # Handle warnings
        err, debug = message.parse_warning() 
        print(err, debug)
 
    return True

GST_PIPELINE = "ximagesrc use-damage=0 ! video/x-raw,framerate=30/1 ! \
   videoconvert ! queue2 ! \
   x264enc bitrate=8000 speed-preset=superfast tune=zerolatency qp-min=30 \
   key-int-max=15 bframes=2 ! video/x-h264,profile=high ! queue2 ! \
   mpegtsmux name=mux ! rndbuffersize max=1316 min=1316 !\
   tcpserversink host=0.0.0.0 recover-policy=keyframe sync-method=latest-keyframe host=0.0.0.0 port=4321 \
   pulsesrc device={0} ! \
   audioconvert ! queue2 ! avenc_aac ! queue2 ! mux. \
".format( get_pulse_device().stdout[:-1] )

if __name__ == "__main__":
    #GObject.threads_init()
    #loop = GObject.MainLoop()
    ip = get_local_ip()
    kodi = "http://xbian:8080"
    loop = GLib.MainLoop()
    Gst.init(None)
    
    pipe = Gst.parse_launch( GST_PIPELINE )
    pipe.set_state(Gst.State.PLAYING)
    
    cast_to_kodi(kodi, ip)
    #thread.start_new_thread(cast_to_kodi, (kodi, ip) )

    print("stream ready at tcp://0.0.0.0:4321")
    loop.run()
