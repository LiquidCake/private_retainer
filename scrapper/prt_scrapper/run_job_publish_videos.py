#!/usr/bin/env python3
import os

from scrapper_job.constants import *

if not 'PRT_ENV' in os.environ:
    os.environ['PRT_ENV'] = 'dev'

if os.environ['PRT_ENV'] == 'dev':
    os.environ['ENV_FILE_PATH'] = '.env.local'

from scrapper_job.scrapper_job import start_scrapper_job

if __name__ == '__main__':
    start_scrapper_job(JOB_TYPE_PUBLISH_VIDEOS, {})