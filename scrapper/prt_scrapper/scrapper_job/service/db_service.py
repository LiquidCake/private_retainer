import os
from datetime import datetime
from functools import lru_cache
import logging as log
from sqlalchemy import orm, create_engine
from sqlalchemy.ext.declarative import declarative_base
from multiprocessing import current_process

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_common.db_common_repository import commit_session, check_exists_by_provider_video_ids_list, get_all_provider_ids, \
    get_configs_by_names_dict, get_found_videos_by_status_ids, update_found_videos
from scrapper_common.models import ScrapperJobLog, ScrapperJobStatus, ScrapperDataTarget, ScrapperDataTargetParsingCode, FoundVideo

DB_URL = 'postgresql://' + os.environ.get('POSTGRES_USER') + ':' + os.environ.get('POSTGRES_PASSWORD') \
    + '@' + os.environ.get('POSTGRES_HOST') + ':' + os.environ.get('POSTGRES_PORT') + '/' + os.environ.get('POSTGRES_DB')

db_engine_per_process = {}

def create_db_engine_for_process():
    base = declarative_base()
    engine = create_engine(DB_URL)
    base.metadata.bind = engine
    session = orm.scoped_session(orm.sessionmaker())(bind=engine)

    db_engine = {
        'base': base,
        'engine': engine,
        'session': session
    }

    return db_engine

def get_session():
    process_name = current_process().name

    if not process_name in db_engine_per_process:
        db_engine_per_process[process_name] = create_db_engine_for_process()
    
    return db_engine_per_process[process_name]['session']

def dispose_engine(process_name):
    if process_name in db_engine_per_process:
        db_engine_per_process[process_name]['engine'].dispose()

#configs

@lru_cache(maxsize=1)
def get_configs_by_names_dict_cached():
    return get_configs_by_names_dict(session=get_session())

#base info

@lru_cache(maxsize=1)
def get_all_provider_ids_cached():
    return get_all_provider_ids(get_session())

#job running

def try_start_job(job_type):

    job_lock_record = get_session().query(ScrapperJobStatus)\
        .filter(ScrapperJobStatus.job_type == job_type, ScrapperJobStatus.status == JOB_STATUS_FINISHED).first()
    
    if job_lock_record == None:
        return None

    new_run_num = job_lock_record.run_num + 1

    rows_updated = get_session().query(ScrapperJobStatus)\
        .filter(ScrapperJobStatus.job_type == job_type, ScrapperJobStatus.status == JOB_STATUS_FINISHED,\
            ScrapperJobStatus.run_num == job_lock_record.run_num)\
        .update({'status': JOB_STATUS_STARTED, 'run_num': new_run_num,\
             'started_at': datetime.now(), 'finished_at': None, 'finish_code': None})

    commit_session(session=get_session())

    if rows_updated == 1:
        return new_run_num
    else:
        return None

def release_job(job_run_num, job_type, finish_code):
    rows_updated = get_session().query(ScrapperJobStatus)\
        .filter(ScrapperJobStatus.job_type == job_type, ScrapperJobStatus.status == JOB_STATUS_STARTED,\
            ScrapperJobStatus.run_num == job_run_num)\
        .update({'status': JOB_STATUS_FINISHED, 'finished_at': datetime.now(), 'finish_code': finish_code})
    
    commit_session(session=get_session())

    if rows_updated != 1:
        msg = 'failed to release lock. Job type: {}, run_num: {}'.format(job_type, job_run_num)
        log.error(msg);
        raise Exception(msg)

def write_job_log(message, job_run_num, job_type):
    now = datetime.now()

    new_log_record = ScrapperJobLog()
    new_log_record.job_type = job_type
    new_log_record.run_num = job_run_num
    new_log_record.log_line = '[' + job_type + ' - #' + str(job_run_num) + ']: ' + message
    new_log_record.created_at = now

    get_session().add(new_log_record)

    commit_session(session=get_session())

    log.info(new_log_record.log_line);

#data targets

def get_scrapper_data_targets(provider_id, target_type_ids=None):
    if target_type_ids == None:
        return get_session().query(ScrapperDataTarget).filter(ScrapperDataTarget.provider_id == provider_id).all()
    else:
        return get_session().query(ScrapperDataTarget)\
            .filter(ScrapperDataTarget.provider_id == provider_id)\
            .filter(ScrapperDataTarget.target_type_id.in_(target_type_ids))\
            .all()

def get_scrapper_data_target_by_ids(target_ids):
    return get_session().query(ScrapperDataTarget).filter(ScrapperDataTarget.target_id.in_(target_ids)).all()

@lru_cache(maxsize=256)
def get_scrapper_data_targets_parsing_code_dict_cached(provider_id):
    return get_scrapper_data_targets_parsing_code(provider_id)

def get_scrapper_data_targets_parsing_code(provider_id):
    return get_session().query(ScrapperDataTargetParsingCode)\
        .filter(ScrapperDataTargetParsingCode.provider_id == provider_id).all()

def update_data_target_meta(target, last_scrapped_provider_video_id, scrapper_script_run_type):
    target.last_scrapped_provider_video_id = last_scrapped_provider_video_id
    target.last_scrapped_at = datetime.now()

    if scrapper_script_run_type == SCRAPPER_SCRIPT_RUN_TYPE_FULL:
            target.last_fully_scrapped_at = target.last_scrapped_at

    get_session().merge(target)
    commit_session(session=get_session())

#found video

def get_found_videos_by_statuses(status_ids, session=None):
    return get_found_videos_by_status_ids(status_ids, session=get_session())

def exists_by_provider_video_ids_list(provider_video_ids, provider_id):
    return check_exists_by_provider_video_ids_list(provider_video_ids, provider_id, get_session())

def update_found_video_items(found_videos):
    update_found_videos(found_videos, get_session())

def persist_video_item_info_list(video_item_info_list, provider_id, video_type_id, target_type_id):
    converted_models = list(map(lambda vi: convert_video_item_info_to_model(vi, provider_id, video_type_id, target_type_id), video_item_info_list))
    
    get_session().bulk_save_objects(converted_models)

    commit_session(session=get_session())

def convert_video_item_info_to_model(video_item_info, provider_id, video_type_id, target_type_id):
    converted = FoundVideo()

    converted.provider_video_id = video_item_info.provider_video_id
    converted.url = video_item_info.video_url
    converted.embed_url = video_item_info.embed_url
    converted.title = video_item_info.video_title
    converted.orig_title = video_item_info.video_title
    converted.video_type_id = video_type_id
    converted.target_type_id = target_type_id
    converted.provider_id = provider_id
    converted.channel_name = video_item_info.channel_name
    converted.channel_id = video_item_info.channel_id
    converted.video_status_id = VIDEO_STATUS_ID_SUPPRESSED if video_item_info.is_suppressed else VIDEO_STATUS_ID_UNAPPROVED
    converted.category_ids = []

    return converted
