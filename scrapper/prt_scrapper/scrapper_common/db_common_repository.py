from sqlalchemy import or_, asc, desc
from sqlalchemy.sql.expression import nullslast

from scrapper_common.constants import *
from scrapper_common.models import FoundVideo, VideoProvider, VideoStatus, VideoType, VideoCategory, Configuration, ScrapperDataTargetType

DB_ROWS_PER_PAGE = 50

def commit_session(session=None):
    session.commit()

def get_found_videos_filtered(video_status_id=None, video_type_id=None, target_type_id=None, video_provider_id=None, \
    video_channel_name=None, video_title=None, page=None, sort_by='created_at', sort_order='DESC', session=None):
    filters = []

    if video_status_id != None:
        filters.append(FoundVideo.video_status_id == video_status_id)

    if video_type_id != None:
        filters.append(FoundVideo.video_type_id == video_type_id)
    
    if target_type_id != None:
        filters.append(FoundVideo.target_type_id == target_type_id)

    if video_provider_id != None:
        filters.append(FoundVideo.provider_id == video_provider_id)
    
    if video_channel_name:
        filters.append(or_(getattr(FoundVideo, 'channel_name').ilike('%' + video_channel_name + '%'), \
            getattr(FoundVideo, 'channel_id').ilike('%' + video_channel_name + '%')))

    if video_title:
        filters.append(or_(getattr(FoundVideo, 'title').ilike('%' + video_title + '%'), \
            getattr(FoundVideo, 'orig_title').ilike('%' + video_title + '%')))

    direction = desc if sort_order == 'DESC' else asc

    query = session.query(FoundVideo) \
        .filter(*filters) \
        .order_by(nullslast(direction(getattr(FoundVideo, sort_by)))).order_by(FoundVideo.video_id)

    if page != None:
        return query.paginate(page=page, per_page=DB_ROWS_PER_PAGE)
    else:
        return query.paginate(page=page, per_page=99999999999)

def check_exists_by_provider_video_ids_list(provider_video_ids, provider_id, session=None):
    return [v.provider_video_id for v in 
        session.query(FoundVideo.provider_video_id) 
            .filter(FoundVideo.provider_id == provider_id)
            .filter(FoundVideo.provider_video_id.in_(provider_video_ids)).all()
    ]

def get_found_video_by_id(video_id, session=None):
    return session.query(FoundVideo).filter(FoundVideo.video_id == video_id).first()

def get_found_videos_by_status_ids(status_ids, session=None):
    return session.query(FoundVideo).filter(FoundVideo.video_status_id.in_(status_ids)).all()

def update_found_videos(found_videos, session=None):
    for vid in found_videos:
        session.merge(vid)

    commit_session(session=session)

def get_video_providers(session=None):
    return session.query(VideoProvider).all()

def get_video_statuses(session=None):
    return session.query(VideoStatus).all()

def get_video_types(session=None):
    return session.query(VideoType).all()

def get_scrapper_target_types(session=None):
    return session.query(ScrapperDataTargetType).all()

def get_video_categories(session=None):
    return session.query(VideoCategory).all()

def get_all_provider_ids(session=None):
    return list(map(lambda p: p.provider_id, get_video_providers(session)))

#configs

def get_configs_by_names(config_name_list=None, session=None):
    if config_name_list != None:
        return session.query(Configuration).filter(Configuration.config_name.in_(config_name_list)).all()
    else:
        return session.query(Configuration).all()

def get_configs_by_names_dict(config_name_list=None, session=None):
    config_dict_provider_aware = {}

    all_configs = get_configs_by_names(config_name_list, session)
    all_provider_ids = get_all_provider_ids(session=session)

    for cfg in all_configs:
        if not cfg.config_name in config_dict_provider_aware:
            config_dict_provider_aware[cfg.config_name] = {}

        per_providers_config_values = config_dict_provider_aware[cfg.config_name]

        if cfg.provider_id == APP_CONFIG_ANY_PROVIDER:
            per_providers_config_values[cfg.provider_id] = cfg.config_value

            for provider_id in all_provider_ids:
                per_providers_config_values[provider_id] = cfg.config_value


    for cfg in all_configs:
        per_providers_config_values = config_dict_provider_aware[cfg.config_name]

        if cfg.provider_id != APP_CONFIG_ANY_PROVIDER:
            per_providers_config_values[cfg.provider_id] = cfg.config_value

    return config_dict_provider_aware

def update_config_value(config_name, provider_id, config_value, session):
    config = session.query(Configuration)\
        .filter(Configuration.config_name == config_name)\
        .filter(Configuration.provider_id == provider_id)\
        .first()
    
    if not config:
        config = session.query(Configuration)\
            .filter(Configuration.config_name == config_name)\
            .filter(Configuration.provider_id == APP_CONFIG_ANY_PROVIDER)\
            .first()

    if not config:
        return 0
    
    else:
        config.config_value = config_value
        commit_session(session=session)

        return 1
