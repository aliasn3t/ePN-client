# -*- coding: utf-8 -*-

import json
import threading
import time
import six
import logging
from requests import Request, Session, RequestException

class init(object):
    request_delay = 1 / 10

    def __init__(self, username = None, password = None, check_ip = None,
                grant_type = 'password', client_id = 'web-client', client_secret = '60cfb46215e4058f39e69c1f4a103e4c'):

        self.logger = logging.getLogger('ePN-client')
        
        self.login = username
        self.password = password
        self.check_ip = check_ip

        self.x_ssid = None
        self.access_token = None
        self.refresh_token = None

        self.x_api_version = '2'
        self.grant_type = grant_type
        self.client_id = client_id
        self.client_secret = client_secret

        self.http = Session()   
        self.http.headers.update({
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
            })

        self.last_request = 0.0
        self.wait = threading.Lock()

    def session(self):
        if not self.x_ssid:
            self._auth_token()

    def _auth_token(self):
        """ Получение токенов """

        self.logger.info('Checking config data...')
        with open('epn.json', 'r') as config:
            cfg = json.load(config)

        if cfg['data']['access_token'] and cfg['data']['refresh_token']:
            self.access_token = cfg['data']['access_token']
            self.refresh_token = cfg['data']['refresh_token']
            if not self._check_token():
                self._token_refresh()
        else:
            self._ssid()

    def _check_token(self):
        """ Проверка токена """

        url = 'https://app.epn.bz/user/profile'

        response = self.http.get(
            url,
            params = {
                'v': self.x_api_version
            },
            headers = {
                'x-access-token': self.access_token,
                'x-api-version': self.x_api_version,
                'content-type': 'application/json'
                }
        )

        if response.ok:
            self.logger.info('access_token is valid')
            return True
        else:
            self.logger.info('access_token is not valid')
            return False

    def _save_session(self):
        """ Сохранение токенов в файл """

        self.logger.info('Saving new config data...')
        config_file = 'epn.json'
        with open(config_file, 'r') as config:
            cfg = json.load(config)

        cfg['data']['access_token'] = self.access_token
        cfg['data']['refresh_token'] = self.refresh_token

        with open(config_file, 'w') as config:
            json.dump(cfg, config)

    def _token_refresh(self):
        """ Обновление токена """

        self.logger.info('Refreshing access_token...')

        url = 'https://oauth2.epn.bz/token/refresh'

        payload = {
            "grant_type": 'refresh_token',
            "refresh_token": self.refresh_token,
            'client_id': self.client_id
            }

        headers = {
            'x-api-version': self.x_api_version,
            'content-type': 'application/json'
            }

        response = self.http.post(
            url,
            data = json.dumps(payload),
            headers = headers
        )

        if response.ok:
            self.logger.info('access_token updated')
            response = response.json()
            self.access_token = response['data']['attributes']['access_token']
            self.refresh_token = response['data']['attributes']['refresh_token']
            self._save_session()
            return True
        else:
            self.logger.info('refresh_token is not valid')
            self._ssid()
            return False

    def _ssid(self):
        """ Получение SSID """

        self.logger.info('Getting SSID...')

        url = 'https://oauth2.epn.bz/ssid'

        response = self.http.get(
            url,
            params = {
                'client_id': self.client_id
                },
            headers = {
                'x-api-version': self.x_api_version
                }
        )

        if response.ok:
            self.logger.info('SSID received')
            response = response.json()
            self.x_ssid = response['data']['attributes']['ssid_token']
            self._jwt_auth()
        else:
            self.logger.error('Error code: {}'.format(response.status_code))
            raise EpnApiException(**response.json()["errors"][0])

    def _jwt_auth(self):
        """ Авторизация """

        self.logger.info('Getting JWT...')

        url = 'https://oauth2.epn.bz/token'

        payload = {
            "grant_type": self.grant_type,
            "username": self.login,
            "password": self.password,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "check_ip": self.check_ip
            }

        headers = {
            'x-api-version': self.x_api_version,
            'x-ssid': self.x_ssid,
            'content-type': 'application/json'
            }

        response = self.http.post(
            url,
            data = json.dumps(payload),
            headers = headers
        )

        if response.ok:
            self.logger.info('Tokens received')
            response = response.json()
            self.access_token = response['data']['attributes']['access_token']
            self.refresh_token = response['data']['attributes']['refresh_token']
            self._save_session()
        else: 
            self.logger.error('Error code: {}'.format(response.status_code))
            raise EpnApiException(**response.json()["errors"][0])

    def api(self):
        return EpnApiMethod(self)

    def method(self, params, values = None):
        """ Обработка запроса """

        query_params = params.split('.')
        type = query_params[0].lower()
        method = query_params[1].lower()

        url = 'https://app.epn.bz'

        get_methods = {
            'balance': '/purses/balance',           # api.get.balance()
            'deeplinks': '/creatives/deeplinks',    # api.get.deeplinks()
            'epn_stat': '/stats/overall',           # api.get.epn_stat()
            'user_info': '/test/user-info',         # api.get.user_info()
            'transactions': '/transactions/user',   # api.get.transactions(tsFrom = '2019-12-23', tsTo = '2020-12-24', perPage = 1000)
            'check_link': '/affiliate/checkLink',   # api.get.check_link(link = 'https://aliexpress.ru/item/4000581767061.html')
            'short_domains': '/link-reduction/domain-cutter-list', # api.get.short_domains()
            'payments': '/user/payment/init',       # api.get.payments()
            'purses': '/user/purses/list'           # api.get.purses()
        }

        post_methods = {
            'create_creative': '/creative/create',  # api.post.create_creative(link = 'https://aliexpress.ru/item/4000581767061.html', offerId = 1, description = 'test_deeplink', type = 'deeplink')
            'short_link': '/link-reduction',        # api.post.short_link(urlContainer = 'https://aliexpress.ru/item/4000581767061.html', domainCutter = 'ali.pub')
            'payment_order': '/user/payment/order', # api.post.payment_order(currency = 'USD', purseId = 1, amount = 1000)
            'logout_client_id': '/logout',          # api.post.logout_client_id(client_id = 'asdfg')
            'logout_refresh_token': '/logout/refresh-token', # api.post.logout_refresh_token(refresh_token = 'asdfg', client_id = 'asdfg')
            'logout_all': '/logout/all'             # api.post.logout_all(client_id = 'asdfg')
        }

        values = values.copy() if values else {}

        if self.access_token:
            self.http.headers.update({
                'x-access-token': self.access_token
                })
            
        with self.wait:
            delay = self.request_delay - (time.time() - self.last_request)

            if delay > 0:
                time.sleep(delay)

            if type == 'get':
                request = Request(method = "GET", url = url + get_methods[method], params = values)
                prepared = self.http.prepare_request(request)

            elif type == 'post':
                request = Request(method = "POST", url = url + post_methods[method], data = values)
                prepared = self.http.prepare_request(request)

            response = self.http.send(prepared)
            self.last_request = time.time()

        if response.ok:
            self.logger.info('{} request ({}) completed'.format(type, method))
            return response.json()
        else:
            if response.status_code == 401:
                if self._token_refresh():
                    response = self.http.send(prepared)
                    if response.ok:
                        self.logger.info('{} second request ({}) completed'.format(type, method))
                        return response.json()
                    else:
                        self.logger.error('{} second request returned error code: {}'.format(params, response.status_code))
                        raise EpnApiException(**response.json()["errors"][0])
            else:
                self.logger.error('{} returned error code: {}'.format(params, response.status_code))
                raise EpnApiException(**response.json()["errors"][0])


class EpnApiMethod(object):
    __slots__ = ('_epn', '_method')

    def __init__(self, epn, method=None):
        self._epn = epn
        self._method = method

    def __getattr__(self, method):
        return EpnApiMethod(
            self._epn, (self._method + '.' if self._method else '') + method
        )

    def __call__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            if isinstance(v, (list, tuple)):
                kwargs[k] = ','.join(str(x) for x in v)

        return self._epn.method(self._method, kwargs)


class EpnApiException(Exception):
    def __init__(self, *args, **kwargs):
        self.error_code = kwargs.get('error', None)
        self.error_description = kwargs.get('error_description', None)

    def __str__(self):
        return 'Error code: {} - {}'.format(self.error_code, self.error_description)