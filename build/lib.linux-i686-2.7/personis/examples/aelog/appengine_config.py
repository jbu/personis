import os
from gaesessions import SessionMiddleware
def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app, 
    	cookie_only_threshold=0,
    	cookie_key='82798247027024730817340831643805710851758016530185638407318043180536158013456310487438047304')
    return app
