#!/usr/bin/env python3
import os

if not 'PRT_ENV' in os.environ:
    os.environ['PRT_ENV'] = 'dev'

debug = False
processes = 4

if os.environ['PRT_ENV'] == 'dev':
     os.environ['ENV_FILE_PATH'] = '.env.local'
     debug = True
     processes = 1

from scrapper_webapp import app

if __name__ == '__main__':
     app.run(host='0.0.0.0', port=8080, debug=debug, threaded=False, processes=processes)
