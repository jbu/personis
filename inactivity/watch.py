#!env python

import sys
sys.path.insert(0, '/home/jbu/personis/server/Src')

import os
import platform
import time
import personis
import json

from oauth2client.file import Storage
from oauth2client.client import Credentials, OAuth2WebServerFlow, flow_from_clientsecrets
from oauth2client.tools import run
import httplib2

osname = os.name + platform.system()
if osname == 'posixLinux':
    import ctypes
    class XScreenSaverInfo( ctypes.Structure):
        """ typedef struct { ... } XScreenSaverInfo; """
        _fields_ = [('window',      ctypes.c_ulong), # screen saver window
                    ('state',       ctypes.c_int),   # off,on,disabled
                    ('kind',        ctypes.c_int),   # blanked,internal,external
                    ('since',       ctypes.c_ulong), # milliseconds
                    ('idle',        ctypes.c_ulong), # milliseconds
                    ('event_mask',  ctypes.c_ulong)] # events

    class idler(object):
        def __init__(self):
            self.xlib = ctypes.cdll.LoadLibrary( 'libX11.so')
            #display_num = os.environ['DISPLAY']
            display_num = ":0"
            self.dpy = self.xlib.XOpenDisplay(display_num)
            if not self.dpy:
                raise Exception('Cannot open display')
            self.root = self.xlib.XDefaultRootWindow( self.dpy)
            self.xss = ctypes.cdll.LoadLibrary( 'libXss.so.1')
            self.xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)
            self.xss_info = self.xss.XScreenSaverAllocInfo()
            self.current = 0

        def getIdleTime(self):
            self.xss.XScreenSaverQueryInfo( self.dpy, self.root, self.xss_info)
            return int(self.xss_info.contents.idle / 1000)

elif osname == 'ntWindows':
    import win32api
    class idler(object):
        def __init__(self):
            self.current = 0
        def getIdleTime(self):
            return win32api.GetLastInputInfo()/1000

elif osname == 'posixDarwin':
    from Quartz.CoreGraphics import CGEventSourceSecondsSinceLastEventType
    # From /System/Library/Frameworks/IOKit.framework/Versions/A/Headers/hidsystem/IOLLEvent.h
    NX_ALLEVENTS = int(4294967295)  # 32-bits, all on.
    class idler(object):
        def getIdleTime(self):
            return CGEventSourceSecondsSinceLastEventType(1, NX_ALLEVENTS)
else:
    raise Error()


def install_inactivity(um):
    try:
        reslist = um.ask(context=["Devices","Inactivity"])
        #return
    except:
        pass

    ctx_obj = personis.Context(Identifier="Inactivity", Description="Watch computer usage",
                 perms={'ask':True, 'tell':True, "resolvers": ["all","last10","last1","goal"]},
                 resolver=None, objectType="Context")
    context = ['Devices']
    um.mkcontext(context,ctx_obj)

    ctx_obj = personis.Context(Identifier="Activity", Description="Extract data from activity watcher",
                 perms={'ask':True, 'tell':True, "resolvers":["all","last10","last1","goal"]},
                 resolver=None, objectType="Context")
    context.append('Inactivity')
    um.mkcontext(context,ctx_obj)

    context.append('Activity')
    cobj = personis.Component(Identifier="length", component_type="attribute", value_type="number",resolver=None,Description="Length of active period")
    um.mkcomponent(context=context, componentobj=cobj)

def send_toggle(um, v, t):
    ev = personis.Evidence(source='activity', evidence_type="explicit", value=v, time=t)
    um.tell(context=['Devices','Inactivity','Activity'], componentid='length', evidence=ev)

inactive_granularity = 5 # seconds
active_granularity = 10 # seconds - you can stop typing for 10 seconds and it's not seen.

if __name__ == '__main__':

    httplib2.debuglevel=0
    storage = Storage('credentials.dat')
    credentials = storage.get()
    FLOW = flow_from_clientsecrets('client_secrets.json',
        scope='https://www.personis.com/auth/model')

    p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
    h = httplib2.Http(proxy_info=p)
    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage, h)
    cjson = json.loads(credentials.to_json())
    http = httplib2.Http(proxy_info=p)
    c = personis.Connection(uri = 'http://ec2-54-251-12-234.ap-southeast-1.compute.amazonaws.com:2005/', 
            credentials = credentials, http = http)

    um = personis.Access(connection=c, debug=True)
    reslist = um.ask(context=["Personal"],view=['firstname'])
    print 'logging for', reslist[0].value

    install_inactivity(um)

    idle = idler();
    time.sleep(1)

    idle_state = True
    i = inactive_granularity + active_granularity
    send_toggle(um, 0, time.time())                

    while True:
        if idle_state:
            while i >= inactive_granularity:
                time.sleep(inactive_granularity)
                i = idle.getIdleTime()
            send_toggle(um, 1, time.time())                
            idle_state = False
        if not idle_state:
            while i < active_granularity:
                time.sleep(active_granularity)
                i = idle.getIdleTime()
            send_toggle(um, 0, time.time())                
            idle_state = True

