import logging as log
import os
import json
import traceback
from datetime import datetime

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_job.service.db_service import write_job_log, get_found_videos_by_statuses, update_found_video_items
from scrapper_job.utils import json_serial


JOB_TYPE = JOB_TYPE_PUBLISH_VIDEOS

OUTPUT_FILE_NAME_TPL = os.environ.get('SCRAPPER_DATA_DIR') + '/published_videos_{}.json'

def run_job(job_run_num, vars):
    try:
        write_job_log('started publish videos job', job_run_num, JOB_TYPE)

        output_file = OUTPUT_FILE_NAME_TPL.format(datetime.now().strftime("%m_%d_%Y_%H_%M_%S"))

        all_approved_videos = get_found_videos_by_statuses([VIDEO_STATUS_ID_APPROVED])
        
        #if some videos are re-approved but uploaded_at timestamp was not cleared 
        # - probably exidentally re-approved, move back to published
        already_published = list(filter(lambda v: v.uploaded_at != None, all_approved_videos))

        videos_to_publish = list(filter(lambda v: v not in already_published, all_approved_videos))
        
        videos_json = json.dumps(list(map(lambda v: v.as_dict(), videos_to_publish)), default=json_serial)

        with open(output_file, 'w') as outfile:
            outfile.write(videos_json)
        
        #set published_at timestamp
        
        for vid in all_approved_videos:
            vid.video_status_id = VIDEO_STATUS_ID_UPLOADED
            vid.uploaded_at = datetime.now()

        update_found_video_items(all_approved_videos)
        
        write_job_log('finished publish videos job, published {} videos'.format(len(videos_to_publish)), job_run_num, JOB_TYPE)

    except Exception as e:
        write_job_log('error during job run: "' + str(e) + '" Trace: ' + traceback.format_exc(), job_run_num, JOB_TYPE)
