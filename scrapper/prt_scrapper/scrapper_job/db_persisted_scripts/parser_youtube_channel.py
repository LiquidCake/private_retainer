import os
import os.path
from os import path
import requests
import random
import time
from selenium.webdriver.common.by import By

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_job.utils import VideoItemInfo, get_worker_log_line, get_data_target_log_line, get_scrapper_script_run_type
from scrapper_job.service.db_service import write_job_log, update_data_target_meta

SCRAPPER_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0'

VIDEO_URL_TEMPLATE = 'https://www.youtube.com/watch?v='
VIDEO_EMBED_URL_TEMPLATE = 'https://www.youtube.com/embed/'

SCRAPPER_URL_RETREIVE_HEADERS = {
    'Host': 'i.ytimg.com',
    'User-Agent': SCRAPPER_USER_AGENT,
    'Accept': 'image/avif,image/webp,*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Alt-Used': 'i.ytimg.com',
    'Referer': 'https://www.youtube.com/',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
    'TE': 'trailers'
}

#86400 is 24h
SCRAPPER_SCRIPT_RUN_TYPE_FULL_DELAY_SEC = 86400

INFINITE_SCROLL_LOAD_WAIT_DELAY_SEC = 2
INFINITE_SCROLL_MAX_LOAD_WAIT_ATTEMPTS = 20

INFINITE_SCROLL_MAX_LOADED_VIDEO_BLOCKS = 10000

def scrap_videos(driver, target, job_run_num, scrapping_worker_id, job_type):
    provider_id = target.provider_id
    target_type_id = target.target_type_id
    target_id = target.target_id
    video_type_id = target.video_type_id
    channel_id = target.channel_id
    channel_name = target.channel_name
    url = target.data_url

    driver.get(url)

    scrapper_script_run_type = get_scrapper_script_run_type(target.last_fully_scrapped_at, SCRAPPER_SCRIPT_RUN_TYPE_FULL_DELAY_SEC)

    video_blocks_loaded = len(find_all_video_blocks(driver))

    write_job_log(get_worker_log_line(get_data_target_log_line(
    'run type: "{}", started page scrolling'.format(scrapper_script_run_type), 
    target_type_id, target_id, video_type_id, channel_id),\
    provider_id, scrapping_worker_id), job_run_num, job_type)

    #iterate infinity scroll till the end or condition
    while True:
        #if this is updates-only run and latest scrapped video is already loaded 
        if scrapper_script_run_type == SCRAPPER_SCRIPT_RUN_TYPE_UPDATES:
            currently_loaded_video_blocks = find_all_video_blocks(driver)
            
            last_scrapped_block_already_loaded = len(list(filter(lambda vb: get_provider_video_id_from_video_block(vb)\
                == target.last_scrapped_provider_video_id, currently_loaded_video_blocks))) > 0
            if last_scrapped_block_already_loaded:
                break

        time.sleep(1)
        new_video_blocks_loaded = infinite_scroll_next_chunk(driver, video_blocks_loaded)

        if new_video_blocks_loaded >= INFINITE_SCROLL_MAX_LOADED_VIDEO_BLOCKS:
            write_job_log(get_worker_log_line(get_data_target_log_line(
            'loaded max amount of video blocks {}, channel is too big, finishing'.format(new_video_blocks_loaded), 
            target_type_id, target_id, video_type_id, channel_id),\
            provider_id, scrapping_worker_id), job_run_num, job_type)
            break
        
        #if reached bottom of infinity scroll
        if new_video_blocks_loaded == video_blocks_loaded:
            break

        video_blocks_loaded = new_video_blocks_loaded    

    #parse video blocks list 

    video_items = []
    video_parent_blocks = find_all_video_blocks(driver)

    write_job_log(get_worker_log_line(get_data_target_log_line(
    'started parsing {} video blocks'.format(len(video_parent_blocks)), 
    target_type_id, target_id, video_type_id, channel_id),\
    provider_id, scrapping_worker_id), job_run_num, job_type)
    
    for video_block in video_parent_blocks:
        provider_video_id = get_provider_video_id_from_video_block(video_block)
        
        if not provider_video_id:
            raise Exception('failed to parse provider_video_id for video block with text "{}"'.format(video_block.text))
        
        video_title = video_block.find_element(By.ID, 'video-title').text

        if not video_title:
            raise Exception('failed to parse video_title for video block with text "{}"'.format(video_block.text))

        preview_img_url = 'https://i.ytimg.com/vi/{}/hqdefault.jpg'.format(provider_video_id)

        video_items.append(
            VideoItemInfo(provider_video_id, video_title, preview_img_url, channel_id, channel_name,
                VIDEO_URL_TEMPLATE + provider_video_id, VIDEO_EMBED_URL_TEMPLATE + provider_video_id)
        )

    #update target meta
    if len(video_items) > 0:
        last_scrapped_provider_video_id = video_items[0].provider_video_id
        update_data_target_meta(target, last_scrapped_provider_video_id, scrapper_script_run_type)

    return video_items

def load_preview_images(video_items, target, job_run_num, scrapping_worker_id, job_type):
    provider_id = target.provider_id
    target_type_id = target.target_type_id
    target_id = target.target_id
    video_type_id = target.video_type_id
    channel_id = target.channel_id

    scrapper_data_dir = os.environ.get('SCRAPPER_DATA_DIR') + '/' + VIDEO_PREVIEW_DIR_NAME
    #keep alive
    session = requests.sessions.Session()

    for video_item in video_items:
        preview_img_file_path = scrapper_data_dir + '/' + str(provider_id) + '-' + video_item.provider_video_id + '.jpg'

        if not path.exists(preview_img_file_path):
            response = url_retrieve(video_item.preview_img_url, session)

            #2nd try
            if not response:
                time.sleep(1)
                response = url_retrieve(video_item.preview_img_url, session)
            
            if response:
                with open(preview_img_file_path, 'wb') as outfile:
                    outfile.write(response.content)

                #throttle request
                time.sleep(random.uniform(0.3, 0.5))
            else:
                write_job_log(get_worker_log_line(get_data_target_log_line(
                'failed to load preview img for video item {}'.format(video_item.provider_video_id), 
                target_type_id, target_id, video_type_id, channel_id),\
                provider_id, scrapping_worker_id), job_run_num, job_type)
                
def url_retrieve(url, session):
    try:
        response = session.get(url, headers=SCRAPPER_URL_RETREIVE_HEADERS, timeout=SCRAPPER_REQUEST_TIMEOUT_SEC)

        if response.ok:
            return response
    except Exception as e:
        return None

def infinite_scroll_next_chunk(driver, video_blocks_loaded):
    driver.execute_script(
        'scrollingElement = (document.scrollingElement || document.body);'
        + 'scrollingElement.scrollTop = scrollingElement.scrollHeight;'
    )
    
    attempt = 1
    while attempt <= INFINITE_SCROLL_MAX_LOAD_WAIT_ATTEMPTS:
        time.sleep(INFINITE_SCROLL_LOAD_WAIT_DELAY_SEC)

        new_video_blocks_loaded = len(find_all_video_blocks(driver))

        if new_video_blocks_loaded > video_blocks_loaded:
            return new_video_blocks_loaded
        
        attempt += 1
    
    return video_blocks_loaded

def get_provider_video_id_from_video_block(video_block):
    local_video_link = video_block.find_element(By.ID, 'video-title-link').get_attribute('href')

    return local_video_link.replace('https://www.youtube.com/watch?v=', '')

def find_all_video_blocks(driver):
    return driver.find_elements(By.TAG_NAME, 'ytd-rich-item-renderer')


#call by passed func name
if call_function == 'scrap_videos':
    return_handle['val'] = scrap_videos(web_driver, target, job_run_num, scrapping_worker_id, job_type)

elif call_function == 'load_preview_images':
    return_handle['val'] = load_preview_images(scrapped_video_items, target, job_run_num, scrapping_worker_id, job_type)
    
else:
    raise Exception('unknown function name passed: {}'.format(call_function))