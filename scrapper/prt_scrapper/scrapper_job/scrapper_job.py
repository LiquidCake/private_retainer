import os
import traceback
import logging as log
from dotenv import load_dotenv

env_file_override = os.environ.get('ENV_FILE_PATH')

load_dotenv(env_file_override if env_file_override else '.env')

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_job.utils import get_required_config_bool
from scrapper_job.service.db_service import try_start_job, release_job, write_job_log

from scrapper_job.jobs import job_scrapper_root
from scrapper_job.jobs import job_scrapper_targets_list
from scrapper_job.jobs import job_publish_videos

log.basicConfig(level=log.INFO)
# sql queries logging
#log.getLogger('sqlalchemy.engine').setLevel(log.INFO)

def start_scrapper_job(job_type, vars):
    log.info('scrapper %s job starting', job_type);
    
    if not get_required_config_bool(APP_CONFIG_SCRAPPER_JOB_ENABLED_PREFIX + '-' + job_type):
        log.warning('scrapper %s job is disabled, exiting', job_type);
        return
    
    job_run_num = try_start_job(job_type)
    if job_run_num == None:
        log.warning('cannot aquire lock for scrapper %s job, exiting', job_type);
        return

    job_finish_code = None

    try:
        write_job_log('started job', job_run_num, job_type)

        job_func = getattr( __import__('scrapper_job').jobs, 'job_' + job_type).run_job
        job_finish_code = job_func(job_run_num, vars)

        write_job_log('finished job', job_run_num, job_type)
    except Exception as e:
        job_finish_code = FINISH_CODE_FAIL
        
        write_job_log('error during job run: "' + str(e) + '" Trace: ' + traceback.format_exc(), job_run_num, job_type)
    finally:
        release_job(job_run_num, job_type, job_finish_code)