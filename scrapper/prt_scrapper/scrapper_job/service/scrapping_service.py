import os
import pathlib
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_job.utils import format_exception_str, get_worker_log_line, get_data_target_log_line
from scrapper_job.service.db_service import write_job_log, get_scrapper_data_targets_parsing_code_dict_cached,\
    exists_by_provider_video_ids_list, persist_video_item_info_list

def scrap_and_store_data(provider_id, job_run_num, scrapping_worker_id, data_targets, job_type):
    targets_parsing_code_list = get_scrapper_data_targets_parsing_code_dict_cached(provider_id)

    web_driver = create_web_driver()
    
    unprocessed_target_ids = []
    try:
        for target in data_targets:
            provider_id = target.provider_id
            target_type_id = target.target_type_id
            target_id = target.target_id
            video_type_id = target.video_type_id
            channel_id = target.channel_id

            #scrap data source

            parsing_code = next(filter(lambda pc: pc.target_type_id == target_type_id and pc.video_type_id == video_type_id,\
                 targets_parsing_code_list), None)

            if parsing_code == None:
                write_job_log(get_worker_log_line(get_data_target_log_line(
                    'parsing code for target not found, skipping data target', 
                    target_type_id, target_id, video_type_id, channel_id),\
                    provider_id, scrapping_worker_id), job_run_num, job_type)
                continue

            try:
                write_job_log(get_worker_log_line(get_data_target_log_line(
                'started scrapping data target', 
                target_type_id, target_id, video_type_id, channel_id),\
                provider_id, scrapping_worker_id), job_run_num, job_type)

                #scrap data target
                return_handle = {}
                exec(parsing_code.parsing_code, {'call_function': 'scrap_videos', 'return_handle': return_handle,
                    'web_driver': web_driver, 'target': target, 'job_run_num': job_run_num, 
                    'scrapping_worker_id': scrapping_worker_id, 'job_type': job_type})

                #DEBUG - comment above, uncomment below, comment/uncomment 2nd 'exec' statement in below try block.
                #  Change below import for script file name you're going to debug,
                #  comment bottom content of script file (all below '#call by passed func name')
                # from scrapper_job.db_persisted_scripts.parser_tiktok_channel_shorts import scrap_videos, load_preview_images
                # return_handle['val'] = scrap_videos(web_driver, target, job_run_num, scrapping_worker_id, job_type)

                scrapped_video_items = return_handle['val']

                try:
                    write_job_log(get_worker_log_line(get_data_target_log_line(
                    'started loading preview images for {} scrapped videos'.format(len(scrapped_video_items)), 
                    target_type_id, target_id, video_type_id, channel_id),\
                    provider_id, scrapping_worker_id), job_run_num, job_type)

                    #load preview images
                    return_handle = {}
                    exec(parsing_code.parsing_code, {'call_function': 'load_preview_images', 'return_handle': return_handle, 
                        'scrapped_video_items': scrapped_video_items, 'target': target, 'job_run_num': job_run_num, 
                        'scrapping_worker_id': scrapping_worker_id, 'job_type': job_type})

                    # return_handle['val'] = load_preview_images(scrapped_video_items, target, job_run_num, scrapping_worker_id, job_type)
                    
                except Exception as e:
                    write_job_log(get_worker_log_line(get_data_target_log_line(
                    'failed to download video preview images: {}'.format(format_exception_str(e)), 
                    target_type_id, target_id, video_type_id, channel_id),\
                    provider_id, scrapping_worker_id), job_run_num, job_type)
                
                write_job_log(get_worker_log_line(get_data_target_log_line(
                'started saving {} scrapped videos into DB'.format(len(scrapped_video_items)), 
                target_type_id, target_id, video_type_id, channel_id),\
                provider_id, scrapping_worker_id), job_run_num, job_type)

                #convert\store videos to DB
                persist_scrapped_videos(scrapped_video_items, provider_id, job_run_num, scrapping_worker_id, target_type_id, target_id,\
                    video_type_id, channel_id, job_type)

            except Exception as e:
                write_job_log(get_worker_log_line(get_data_target_log_line(
                'error during scrapping data target: {}'.format(format_exception_str(e)), 
                target_type_id, target_id, video_type_id, channel_id),\
                provider_id, scrapping_worker_id), job_run_num, job_type)

                unprocessed_target_ids.append(target_id)

                continue

        if len(unprocessed_target_ids) > 0:
            write_job_log(get_worker_log_line(get_data_target_log_line(
            'failed scrapping for data targets : {}'.format(unprocessed_target_ids), 
            target_type_id, target_id, video_type_id, channel_id),\
            provider_id, scrapping_worker_id), job_run_num, job_type)

            return FINISH_CODE_FAIL
        
        return FINISH_CODE_OK
        
    finally:
        if web_driver:
            web_driver.quit()

def create_web_driver():
    options = Options()
    #options.binary_location = FIREFIX_BINARY_LOCATION
    options.add_argument('--headless')
    
    current_dir = str(pathlib.Path(__file__).parent.resolve())

    #log_path='/var/prt-scrapper-data/log.log'
    driver = webdriver.Firefox(service=Service(current_dir + '/webdriver/' + DRIVER_FILE, log_path=os.devnull), options=options)
    driver.set_page_load_timeout(SCRAPPER_REQUEST_TIMEOUT_SEC)

    return driver

def persist_scrapped_videos(video_items, provider_id, job_run_num, scrapping_worker_id, target_type_id, target_id,\
    video_type_id, channel_id, job_type):

    scrapped_provider_video_ids = list(map(lambda v: v.provider_video_id, video_items))
    persisted_provider_video_ids = exists_by_provider_video_ids_list(scrapped_provider_video_ids, provider_id)

    video_items_to_persist = list(filter(lambda v: not v.provider_video_id in persisted_provider_video_ids, video_items))

    persist_video_item_info_list(video_items_to_persist, provider_id, video_type_id, target_type_id)

    write_job_log(get_worker_log_line(get_data_target_log_line(
    'saved {} newly-found video items into DB'.format(len(video_items_to_persist)), 
    target_type_id, target_id, video_type_id, channel_id),\
    provider_id, scrapping_worker_id), job_run_num, job_type)

