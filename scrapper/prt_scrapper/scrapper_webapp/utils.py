from scrapper_common.constants import *
from scrapper_webapp.db_service import get_configs_by_names_dict_uncached

def get_config_uncached(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    configs_by_name_and_provider = get_configs_by_names_dict_uncached()
    
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

def get_required_config_string_uncached(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    config_value = get_config_uncached(config_name, provider_id)

    if config_value == None:
        raise Exception('config not found: {0} for provider_id: {1}', \
            config_name, provider_id)
    return config_value

def get_required_config_int_uncached(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    return int(get_required_config_string_uncached(config_name, provider_id=provider_id))

def get_required_config_bool_uncached(config_name, provider_id=APP_CONFIG_ANY_PROVIDER):
    return bool(get_required_config_string_uncached(config_name, provider_id=provider_id))