import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VaultClient:
    def __init__(self, vault_access_token:str, vault_api_endpint:str,  default_group:str, env:str="prod",cache_timeout=600):
        self.default_group = default_group
        self.vault_access_token=vault_access_token
        self.vault_api_endpint=vault_api_endpint
        self.cache_timeout=cache_timeout
        self.env = env
        self.__cache = {}

    def is_true(self,  key:str, default_value:str=None, group:str=None):
        val = self.get(key=key, default_value=default_value, group=group)
        return val in ('True','Yes', 'yes', '1')

    def is_enabled(self,  key:str, default_value:str=None, group:str=None):
        return self.is_true(key=key, default_value=default_value, group=group)

    def get(self, key:str, default_value:str=None, group:str=None):
        """
        Get the value for key. If no group is provided, the default group for this instance is used. 
        If value is not found, default_value will be returned
        """

        group = group if group else self.default_group

        logger.debug(f'Getting settings {group}-> {key}')

        group_vars = self.__get_or_set(f'__vault_{group}_{self.env}', lambda: self.__fetch_from_server(group=group), timeout=self.cache_timeout)
        if group_vars and key in group_vars:
            return group_vars[key] or default_value
        else:
            return default_value


    def __get_or_set(self, cache_key:str, default_val_func, timeout):

        logger.debug(f'Getting from cache key {cache_key}')

        current_value = self.__cache.get(cache_key, None)
        if not current_value or current_value['timeout'] < datetime.utcnow() and callable(default_val_func):

            logger.debug(f'Cache missed, load from given source')

            current_value ={
                'value': default_val_func(),
                'timeout': datetime.utcnow() + timedelta(seconds=timeout)
            }

            self.__cache[cache_key] = current_value
        else:
            logger.debug(f'Found data in cahe, returning')

        return current_value['value']



    def __fetch_from_server(self, group:str):

        logger.debug(f'Cache missed, fething from source {self.vault_api_endpint}')
        try:
            response = requests.get(url=f'{self.vault_api_endpint}/api/configs/{self.env}/{group}/',
                                   headers={'Authorization': f'Bearer {self.vault_access_token}'},
                                   timeout=5)
            
            
            if response.ok:
                logger.debug(f'Response came successfully. {response.json()}')
                return response.json()

        except requests.ConnectionError as ex:
            print(f'Connection error: {ex}')
        except requests.RequestException as exx:
            print(f'Request error: {exx}')

        return {}


    def output_html(self):
        html=[]
        for k,v in self.__cache.items():
            html.append(f'<div><strong>{k.upper()}:</strong> {v}</div>')
        return ''.join(html)

