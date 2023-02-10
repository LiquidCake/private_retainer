from multiprocessing import Process, Queue, current_process

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_job.utils import get_required_config_int, partition_list, format_exception_str, get_worker_log_line
from scrapper_job.service.db_service import get_all_provider_ids_cached, get_scrapper_data_targets, write_job_log, dispose_engine
from scrapper_job.service.scrapping_service import scrap_and_store_data

worker_return_values = []

def run_job(job_run_num, vars):
    all_provider_ids = get_all_provider_ids_cached()
    
    worker_processes = []
    return_val_queue = Queue()
    return_val_queue.put(worker_return_values)

    write_job_log('launching workers', job_run_num, JOB_TYPE_ROOT)

    for provider_id in all_provider_ids:
        paralellism_factor = get_required_config_int(APP_CONFIG_SCRAPPER_JOB_DATA_TARGET_PARALLELISM, provider_id)

        data_targets = list(filter(lambda dt: dt.enabled, get_scrapper_data_targets(provider_id)))
        data_targets_chunked_list = partition_list(data_targets, paralellism_factor)
        
        next_scrapping_worker_id = 1

        for data_targets_chunk in data_targets_chunked_list:
            worker_process = Process(target=run_scrapping_worker,\
                args=(return_val_queue, provider_id, job_run_num, next_scrapping_worker_id, data_targets_chunk))

            worker_processes.append(worker_process)
            worker_process.start()

            next_scrapping_worker_id += 1

    write_job_log('launched all workers, waiting for finish', job_run_num, JOB_TYPE_ROOT)

    for worker_process in worker_processes:
        worker_process.join()

    worker_return_messages = return_val_queue.get()

    job_finish_code = FINISH_CODE_OK

    if len(worker_return_messages) != len(worker_processes) or\
        len(list(filter(lambda resp: not resp.endswith(FINISH_CODE_OK), worker_return_messages))) > 0:
        job_finish_code = FINISH_CODE_FAIL

    write_job_log('finished all workers. Finish code: {}, Workers return codes(expected {} responses): {}'\
        .format(job_finish_code, len(worker_processes), str(worker_return_messages)), job_run_num, JOB_TYPE_ROOT)

    dispose_engine(current_process().name)

    return job_finish_code

def run_scrapping_worker(return_val_queue, provider_id, job_run_num, scrapping_worker_id, data_targets):
    finish_code = FINISH_CODE_OK

    try:
        data_targets_ids = list(map(lambda dt: dt.target_id, data_targets))
        write_job_log(get_worker_log_line('started scrapping for data_target_ids: {}'.format(data_targets_ids),\
             provider_id, scrapping_worker_id), job_run_num, JOB_TYPE_ROOT)
        
        finish_code = scrap_and_store_data(provider_id, job_run_num, scrapping_worker_id, data_targets, JOB_TYPE_ROOT)
        
        write_job_log(get_worker_log_line('finished scrapping for data_target_ids: {}'.format(data_targets_ids),\
             provider_id, scrapping_worker_id), job_run_num, JOB_TYPE_ROOT)

    except Exception as e:
        finish_code = FINISH_CODE_FAIL

        write_job_log(get_worker_log_line('error during worker run. {}'.format(format_exception_str(e)),\
            provider_id, scrapping_worker_id), job_run_num, JOB_TYPE_ROOT)

    finally:
        return_values = return_val_queue.get()
        try:
            return_values.append('worker_p-{}_id-{}:{}'.format(provider_id, scrapping_worker_id, finish_code))
            return_val_queue.put(return_values)
        except Exception as e:
            return_val_queue.put(return_values) #unlocks queue. Needed if error was thrown between get and put
        finally:
            dispose_engine(current_process().name)
