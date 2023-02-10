from multiprocessing import current_process

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_job.utils import format_exception_str, get_worker_log_line
from scrapper_job.service.db_service import get_scrapper_data_target_by_ids, write_job_log, dispose_engine
from scrapper_job.service.scrapping_service import scrap_and_store_data

def run_job(job_run_num, vars):
    all_target_ids = vars['data_target_ids']

    all_data_targets = get_scrapper_data_target_by_ids(all_target_ids)

    if len(all_data_targets) == 0:
        write_job_log('error: data targets not found by ids: {}, exiting'.format(all_target_ids), job_run_num, JOB_TYPE_TARGETS_LIST)
        return

    data_targets = list(filter(lambda dt: dt.enabled, all_data_targets))
    if len(data_targets) == 0:
        write_job_log('no ENABLED data targets found by ids: {}, exiting'.format(all_target_ids), job_run_num, JOB_TYPE_TARGETS_LIST)
        return

    target_ids = list(map(lambda dt: dt.target_id, data_targets))
    
    provider_id = data_targets[0].provider_id
    scrapping_worker_id = 1
    finish_code = FINISH_CODE_OK

    try:
        write_job_log('launching targets-list scrapping for provider-id: {} target-ids: {}'.format(provider_id, target_ids),
            job_run_num, JOB_TYPE_TARGETS_LIST)
        
        finish_code = scrap_and_store_data(provider_id, job_run_num, scrapping_worker_id, data_targets, JOB_TYPE_TARGETS_LIST)
        
        write_job_log(get_worker_log_line('finished targets-list scrapping for data_target_ids: {}. Finish code: {}'\
            .format(target_ids, finish_code), provider_id, scrapping_worker_id), job_run_num, JOB_TYPE_TARGETS_LIST)

    except Exception as e:
        finish_code = FINISH_CODE_FAIL

        write_job_log(get_worker_log_line('error during targets-list scrapping worker run. {}'.format(format_exception_str(e)),\
            provider_id, scrapping_worker_id), job_run_num, JOB_TYPE_TARGETS_LIST)

    dispose_engine(current_process().name)

    return finish_code
