#!/usr/bin/env python

import sys

import os
import platform
import time
from personis import client
import json

from oauth2client.file import Storage
from oauth2client.client import Credentials, OAuth2WebServerFlow, flow_from_clientsecrets
from oauth2client.tools import run
import httplib2
import logging
from Queue import Queue
import threading
import math

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
        reslist = um.ask(context=["Devices","activity_monitor"])
        return
    except:
        pass

    ctx_obj = client.Context(Identifier="activity_monitor", Description="Watch computer usage",
                 perms={'ask':True, 'tell':True, "resolvers": ["all","last10","last1","goal"]},
                 resolver=None, objectType="Context")
    context = ['Devices']
    um.mkcontext(context,ctx_obj)
    context.append('activity_monitor')

    ctx_obj = client.Context(Identifier="activity", Description="Extract data from activity watcher",
                 perms={'ask':True, 'tell':True, "resolvers":["all","last10","last1","goal"]},
                 resolver=None, objectType="Context")
    um.mkcontext(context,ctx_obj)
    context.append('activity')

    cobj = client.Component(Identifier="data", component_type="attribute", 
        value_type="number",resolver=None,Description="0 on inactivity detection, 1 on activity detection, -1 on shutdown")
    um.mkcomponent(context=context, componentobj=cobj)

class sender(threading.Thread):
    def __init__(self, um):
        self.q = Queue()
        self.um = um
        self.running = False
        threading.Thread.__init__(self)

    def send(self, v, t):
        ev = client.Evidence(source='activity_monitor', evidence_type="explicit", value=v, time=t)
        self.q.put(ev)
        logging.debug('put %s'%(ev))

    def run(self):
        retries = 1
        self.running = True
        ev = None
        while self.running:
            if ev == None:
                ev = self.q.get(block=True)
                logging.debug('got %s'%(ev))
            try:
                self.um.tell(context=['Devices','activity_monitor','activity'], componentid='data', evidence=ev)
                logging.info('%s: %s'%(time.asctime(time.localtime(ev.time)), ev.value))
                ev = None
                retries = 1
                self.q.task_done()
            except Exception as e:
                backoff = math.sqrt(retries)*4
                logging.info('Personis down? try again in %d seconds'%(backoff))
                time.sleep(backoff)
                retries = retries + 1

    def stop(self):
        self.running = False
        self.q.join()
        threading.Thread.join(self)


def go():
    inactive_granularity = 5 # seconds
    active_granularity = 10 # seconds - you can stop typing for 10 seconds and it's not seen.

    gflags.DEFINE_enum('logging_level', 'ERROR',
        ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        'Set the level of logging detail.')
    gflags.DEFINE_string('clientjson', None, 'client json file', short_name='j')
    # Let the gflags module process the command-line arguments
    try:
        argv = gflags.FLAGS(sys.argv)
    except gflags.FlagsError, e:
        print '%s\\nUsage: %s ARGS\\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)
    #httplib2.debuglevel=0
    logging.getLogger().setLevel(getattr(logging, gflags.FLAGS.logging_level))

    # get past the uni's stupid proxy server
    p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)

    # Use the util package to get a link to UM. This uses the client_secrets.json file for the um location
    if gflags.FLAGS.clientjson is not None:
        client_secrets = gflags.FLAGS.clientjson
    else:
        client_secrets = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
    um = client.util.LoginFromClientSecrets(filename=client_secrets, http=httplib2.Http(proxy_info=p, disable_ssl_certificate_validation=True), credentials='activity_cred.dat')

    reslist = um.ask(context=["Personal"],view=['firstname'])
    #print 'logging for', reslist[0].value

    install_inactivity(um)
    snd = sender(um)
    snd.start()
    idle = idler();
    time.sleep(1)

    idle_state = True
    i = inactive_granularity + active_granularity
    snd.send(0, time.time())                

    try:
        while True:
                if idle_state:
                    while i >= inactive_granularity:
                        time.sleep(inactive_granularity)
                        i = idle.getIdleTime()
                    snd.send(1, time.time())                
                    idle_state = False
                if not idle_state:
                    while i < active_granularity:
                        time.sleep(active_granularity)
                        i = idle.getIdleTime()
                    snd.send(0, time.time())                
                    idle_state = True
    except:
        pass
    finally:
        snd.send(-1, time.time())  
        snd.stop()

if __name__ == '__main__':
    go()