import traceback
from datetime import datetime, date

from scrapper_common.constants import *
from scrapper_job.constants import *
from scrapper_job.service.db_service import get_configs_by_names_dict_cached

class VideoItemInfo:
    def __init__(self, provider_video_id, video_title, preview_img_url, channel_id, channel_name,\
         video_url, embed_url, is_suppressed=False):
        self.provider_video_id = provider_video_id
        self.video_title = video_title
        self.preview_img_url = preview_img_url
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.video_url = video_url
        self.embed_url = embed_url
        self.is_suppressed = is_suppressed
    
    def __repr__(self):
        return '(%s, %s, %s, %s, %s, %s, %s, %s)' % \
            (self.provider_video_id, self.video_title, self.preview_img_url, self.channel_id, \
                self.channel_name, self.video_url, self.embed_url, self.is_suppressed)

def get_config_cached(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    configs_by_name_and_provider = get_configs_by_names_dict_cached()
    
    if config_name in configs_by_name_and_provider:
        per_providers_config_values = configs_by_name_and_provider[config_name]

        if provider_id in per_providers_config_values:
            return per_providers_config_values[provider_id]
        elif APP_CONFIG_ANY_PROVIDER in per_providers_config_values:
            return per_providers_config_values[APP_CONFIG_ANY_PROVIDER]
        else:
            return None

    else:
        return None

def get_required_config_string(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    config_value = get_config_cached(config_name, provider_id)

    if config_value == None:
        raise Exception('config not found: {0} for provider_id: {1}', \
            config_name, provider_id)
    return config_value

def get_required_config_int(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    return int(get_required_config_string(config_name, provider_id=provider_id))

def get_required_config_bool(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    return bool(get_required_config_string(config_name, provider_id=provider_id))

def partition_list(l, chunk_size):
    return [l[i:i + chunk_size] for i in range(0, len(l), chunk_size)];

def format_exception_str(e):
    return 'Error: "{}", Trace: "{}"'.format(str(e), traceback.format_exc())

def get_worker_log_line(message, provider_id, next_scrapping_worker_id):
    return 'scrapping_worker (provider-id: {}, worker-id: {}): {}'\
        .format(provider_id, next_scrapping_worker_id, message)

def get_data_target_log_line(message, target_type_id, target_id, video_type_id, channel_id):
    return 'data_target(target-type-id: {}, target-id: {}, video-type-id: {}, channel-id: {}): {}'\
        .format(target_type_id, target_id, video_type_id, channel_id, message)

def get_scrapper_script_run_type(last_fully_scrapped_at, scrapper_script_full_run_delay_sec):
    if last_fully_scrapped_at == None \
        or (datetime.now() - last_fully_scrapped_at).seconds > scrapper_script_full_run_delay_sec:

        return SCRAPPER_SCRIPT_RUN_TYPE_FULL
    else:
        return SCRAPPER_SCRIPT_RUN_TYPE_UPDATES

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))