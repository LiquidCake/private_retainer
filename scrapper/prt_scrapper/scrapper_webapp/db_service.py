from collections import ChainMap
import json

from scrapper_webapp import cache
from scrapper_webapp import db
from scrapper_common.constants import *
from scrapper_common.db_common_repository import commit_session, get_video_providers, get_video_statuses, get_video_types, \
    get_video_categories, get_found_videos_filtered, get_found_video_by_id, get_scrapper_target_types, get_configs_by_names_dict, update_config_value
from scrapper_common.models import FoundVideo, ScrapperDataTarget

@cache.cached(key_prefix='get_video_providers_info_dict')
def get_video_providers_info_dict():
    list_of_dicts = list(map(lambda m: {m.provider_id: {
        'short_name': m.short_name, 
        'base_url': m.base_url,
        'channel_url_template': m.channel_url_template,
        'preview_img_extension': m.preview_img_extension,
        'embed_type': m.embed_type,
        'video_aspect': m.video_aspect,
        'preview_aspect': m.preview_aspect,
        'additional_data_json': json.loads(m.additional_data_json)
    }}, get_video_providers(session=db.session)))
    return dict(ChainMap(*list_of_dicts))

@cache.cached(key_prefix='get_video_statuses_info_dict')
def get_video_statuses_info_dict():
    list_of_dicts = list(map(lambda m: {m.video_status_id: m.short_name}, get_video_statuses(session=db.session)))
    return dict(ChainMap(*list_of_dicts))

@cache.cached(key_prefix='get_video_types_info_dict')
def get_video_types_info_dict():
    list_of_dicts = list(map(lambda m: {m.video_type_id:  m.short_name}, get_video_types(session=db.session)))
    return dict(ChainMap(*list_of_dicts))

@cache.cached(key_prefix='get_scrapper_target_types_info_dict')
def get_scrapper_target_types_info_dict():
    list_of_dicts = list(map(lambda m: {m.target_type_id:  m.short_name}, get_scrapper_target_types(session=db.session)))
    return dict(ChainMap(*list_of_dicts))

@cache.cached(key_prefix='get_video_categories_info_dict')
def get_video_categories_info_dict():
    list_of_dicts = list(map(lambda m: {m.category_id: m.category_name}, get_video_categories(session=db.session)))
    return dict(ChainMap(*list_of_dicts))

def get_configs_by_names_dict_uncached():
    return get_configs_by_names_dict(session=db.session)

def update_config_val(config_name, provider_id, new_val):
    return update_config_value(config_name, provider_id, new_val, db.session)

def get_found_videos(get_videos_params):
    get_videos_params['session'] = db.session
    return get_found_videos_filtered(**get_videos_params)

def update_video_item_info(video_item_id, new_title, new_video_status_id, new_editor_pick_set, \
        upload_time_clear_set, new_video_category_ids):
    video_item = get_found_video_by_id(video_item_id, session=db.session)
    video_item.title = new_title
    video_item.video_status_id = new_video_status_id
    video_item.editors_pick = new_editor_pick_set
    video_item.uploaded_at = None if upload_time_clear_set else video_item.uploaded_at
    video_item.category_ids = new_video_category_ids

    commit_session(session=db.session)

def ignore_videos_by_channel(channel_id, provider_id):
    rows_updated = db.session.query(FoundVideo)\
        .filter(FoundVideo.provider_id == provider_id, FoundVideo.channel_id == channel_id)\
        .filter(FoundVideo.video_status_id.not_in([VIDEO_STATUS_ID_APPROVED, VIDEO_STATUS_ID_UPLOADED, VIDEO_STATUS_ID_IGNORED]))\
        .update({'video_status_id': VIDEO_STATUS_ID_IGNORED})

    commit_session(session=db.session)

    return rows_updated

def create_scrapper_data_target(channel_id, channel_name, provider_id, video_type_id, channel_data_url, enabled, target_rating):
    existing_data_target = db.session.query(ScrapperDataTarget)\
        .filter(ScrapperDataTarget.data_url == channel_data_url).first()

    if existing_data_target:
        return 0

    new_data_target = ScrapperDataTarget()

    new_data_target.target_type_id = TARGET_TYPE_ID_CHANNEL
    new_data_target.video_type_id = video_type_id
    new_data_target.provider_id = provider_id
    new_data_target.data_url = channel_data_url
    new_data_target.channel_id = channel_id
    new_data_target.channel_name = channel_name
    new_data_target.enabled = enabled
    new_data_target.target_rating = target_rating

    db.session.add(new_data_target)

    commit_session(session=db.session)

    return 1