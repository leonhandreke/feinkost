MONGODB_SETTINGS = {
        'db': 'feinkost',
        'host': None,
        'port': None,
        }

BOOTSTRAP_SERVE_LOCAL = True

SERVER_NAME = '127.0.0.1:5000'

WTF_CSRF_ENABLED = False

try:
    from local_settings import *
except ImportError:
    pass
