import os
if os.path.exists('instance') and os.path.exists('instance/config.py'):
    from instance.config import *

DB_PATH = 'Your sql db url here'
API_KEY = 'Your Google API key here'
