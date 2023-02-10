import os
from flask import request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from scrapper_common.constants import *
from scrapper_webapp import app
from scrapper_webapp import auth
from scrapper_webapp.utils import get_required_config_string_uncached
from scrapper_webapp.db_service import get_video_providers_info_dict, get_video_statuses_info_dict, get_video_types_info_dict, \
    get_video_categories_info_dict, get_found_videos, update_video_item_info, get_scrapper_target_types_info_dict, update_config_val, \
    ignore_videos_by_channel, create_scrapper_data_target

HTTP_STATUS_BAD_REQUEST = 400

PARAM_ALL = 'all'

DEFAULT_VIDEO_STATUS = 'unapproved'
DEFAULT_VIDEO_TYPE = 'all'
DEFAULT_TARGET_TYPE = 'all'
DEFAULT_VIDEO_PROVIDER = 'all'

DEFAULT_SORT_BY = 'created_at'
DEFAULT_SORT_ORDER = 'DESC'

http_basic_auth_username = os.environ.get('HTTP_BASIC_AUTH_USERNAME')
http_basic_auth_password = os.environ.get('HTTP_BASIC_AUTH_PASSWORD')

users = {
    http_basic_auth_username: generate_password_hash(http_basic_auth_password)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

@app.route('/')
@auth.login_required
def index():
    lookup_provider = get_video_providers_info_dict()
    lookup_video_status = get_video_statuses_info_dict()
    lookup_video_type = get_video_types_info_dict()
    lookup_target_type = get_scrapper_target_types_info_dict()
    lookup_video_category = get_video_categories_info_dict()

    lookup_provider_by_name = {v['short_name']: k for k, v in lookup_provider.items()}
    lookup_video_status_by_name = {v: k for k, v in lookup_video_status.items()}
    lookup_video_type_by_name = {v: k for k, v in lookup_video_type.items()}
    lookup_target_type_by_name = {v: k for k, v in lookup_target_type.items()}

    video_status = request.args.get('video-status', DEFAULT_VIDEO_STATUS, type=str)
    video_type = request.args.get('video-type', DEFAULT_VIDEO_TYPE, type=str)
    target_type = request.args.get('target-type', DEFAULT_TARGET_TYPE, type=str)
    video_provider = request.args.get('video-provider', DEFAULT_VIDEO_PROVIDER, type=str)
    video_channel_name = request.args.get('video-channel-name', '', type=str).strip()
    video_title = request.args.get('video-title', '', type=str).strip()

    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort-by', DEFAULT_SORT_BY, type=str)
    sort_order = request.args.get('sort-order', DEFAULT_SORT_ORDER, type=str)

    get_videos_params = {'video_channel_name': video_channel_name, 'video_title': video_title,
        'page': page, 'sort_by': sort_by, 'sort_order': sort_order}

    if video_provider != PARAM_ALL:
        get_videos_params['video_provider_id'] = lookup_provider_by_name[video_provider]
 
    if video_status != PARAM_ALL:
        get_videos_params['video_status_id'] = lookup_video_status_by_name[video_status]

    if video_type != PARAM_ALL:
        get_videos_params['video_type_id'] = lookup_video_type_by_name[video_type]
    
    if target_type != PARAM_ALL:
        get_videos_params['target_type_id'] = lookup_target_type_by_name[target_type]

    video_items = get_found_videos(get_videos_params)
    
    return render_template('videos-list.html', page_vars={
        'video_items': video_items,
        'lookup_provider': lookup_provider, 'lookup_video_status': lookup_video_status, 'lookup_video_type': lookup_video_type, \
        'lookup_target_type': lookup_target_type, 'lookup_video_category': lookup_video_category, \
        'page_filtering_params': 
            {'video_status': video_status, 'video_type': video_type, 'target_type': target_type, 'video_provider': video_provider, \
            'video_channel_name': video_channel_name, 'video_title': video_title, 'sort_by': sort_by, 'sort_order': sort_order}
    })

@app.route('/update-video-item', methods=['POST'])
@auth.login_required
def update_video_item():
    content = request.json

    video_item_id = int(content['video_item_id'])
    new_title = content['new_title']
    new_video_status_id = int(content['new_video_status_id'])
    new_editor_pick_set = bool(content['new_editor_pick_set'])
    upload_time_clear_set = bool(content['upload_time_clear_set'])
    new_video_category_ids = content['new_video_category_ids']

    #categories field doesnt have foreign key so validate
    lookup_video_category = get_video_categories_info_dict()

    for cat_id in new_video_category_ids:
        if cat_id not in lookup_video_category:
                return 'unknown video category: ' + cat_id, HTTP_STATUS_BAD_REQUEST

    update_video_item_info(video_item_id, new_title, new_video_status_id, new_editor_pick_set, \
        upload_time_clear_set, new_video_category_ids)

    return jsonify({'status': 'ok', 'message': 'ok'})

@app.route('/add-channel-target', methods=['POST'])
@auth.login_required
def add_channel_target():
    content = request.json

    channel_id = content['channel_id']
    channel_name = content['channel_name']
    provider_id = int(content['provider_id'])
    video_type_id = int(content['video_type_id'])

    providers = get_video_providers_info_dict()
    
    channel_data_url = providers[provider_id]['additional_data_json']['data_url_tpl_by_video_type_id'][str(video_type_id)]
    channel_data_url = channel_data_url.format(channel_id)
    
    config_rows_updated = create_scrapper_data_target(channel_id, channel_name, provider_id, video_type_id, channel_data_url, True, DEFAULT_TARGET_RATING)

    if config_rows_updated > 0:
        ignored_video_rows = ignore_videos_by_channel(channel_id, provider_id)

        return jsonify({'status': 'ok', 'message': 'added new channel data target for "{}"'.format(channel_id)})
    else:
        return jsonify({'status': 'error', 'message': 'data target already exists'})


@app.route('/ignore-channel', methods=['POST'])
@auth.login_required
def ignore_channel():
    content = request.json

    channel_id = content['channel_id']
    provider_id = int(content['provider_id'])

    existing_config_list = list(map(lambda ch: ch.strip(), get_required_config_string_uncached(APP_CONFIG_SCRAPPER_IGNORED_CHANNELS, provider_id)\
        .strip().split(',')))

    if len(existing_config_list) == 1 and not existing_config_list[0]:
        existing_config_list = []
    
    if not channel_id in existing_config_list:
        existing_config_list.append(channel_id)

    config_rows_updated = update_config_val(APP_CONFIG_SCRAPPER_IGNORED_CHANNELS, provider_id, ','.join(existing_config_list))

    if config_rows_updated > 0:
        ignored_video_rows = ignore_videos_by_channel(channel_id, provider_id)

        return jsonify({'status': 'ok', 'message': 'ignored videos: {}'.format(ignored_video_rows)})
    else:
        return jsonify({'status': 'error', 'message': 'updated 0 rows'})

#
#jobs
#

@app.route('/start-scrapper-job-root')
@auth.login_required
def start_scrapper_job_root():
    app.logger.info('Starting scrapper root job')
    os.system('./run_job_root.py &')

    return jsonify({'status': 'ok', 'message': 'ok'})

@app.route('/start-scrapper-job-targets-list')
@auth.login_required
def start_scrapper_job_targets_list():
    target_ids_csv = request.args.get('target-ids', '', type=str)
    if not target_ids_csv:
        app.logger.info('Targets list job - got empty target ids list, exiting')
        
        return

    target_ids = list(map(lambda id: id.strip(), target_ids_csv.split(',')))
    
    app.logger.info('Starting scrapper targets list job for %s', target_ids)
    os.system('./run_job_targets_list.py {} &'.format(' '.join(target_ids)))

    return jsonify({'status': 'ok', 'message': 'ok'})

@app.route('/start-scrapper-job-publish-videos')
@auth.login_required
def start_scrapper_job_publish_videos():
    app.logger.info('Starting scrapper publish videos job')
    os.system('./run_job_publish_videos.py &')

    return jsonify({'status': 'ok', 'message': 'ok'})

#
# template filters
#

@app.template_filter()
def format_channel_url(video_item):
    providers = get_video_providers_info_dict()

    return providers[video_item.provider_id]['channel_url_template'].format(video_item.channel_id)

@app.template_filter()
def get_preview_img_extension(video_item):
    providers = get_video_providers_info_dict()

    return providers[video_item.provider_id]['preview_img_extension']

@app.template_filter()
def get_embed_type(video_item):
    providers = get_video_providers_info_dict()

    return providers[video_item.provider_id]['embed_type']

@app.template_filter()
def get_video_aspect(video_item):
    providers = get_video_providers_info_dict()

    return providers[video_item.provider_id]['video_aspect']

@app.template_filter()
def get_preview_aspect(video_item):
    providers = get_video_providers_info_dict()

    return providers[video_item.provider_id]['preview_aspect']