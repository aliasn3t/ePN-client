# -*- coding: utf-8 -*-

import json
import threading
import time
import requests
import six

class init(object):
    request_delay = 0.5

    def __init__(self, username = None, password = None, check_ip = None,
                grant_type = 'password', client_id = 'web-client', client_secret = '60cfb46215e4058f39e69c1f4a103e4c'):
        
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

        self.http = requests.Session()
        self.http.headers.update({
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
            })

        self.last_request = 0.0
        self.wait = threading.Lock()

    def session(self):
        if not self.x_ssid:
            self._auth_token()

    def _auth_token(self):
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
            return True
        else: 
            return False

    def _save_session(self):
        """ Сохранение токенов в файл """

        config_file = 'epn.json'
        with open(config_file, 'r') as config:
            cfg = json.load(config)

        cfg['data']['access_token'] = self.access_token
        cfg['data']['refresh_token'] = self.refresh_token

        with open(config_file, 'w') as config:
            json.dump(cfg, config)

    def _token_refresh(self):
        """ Обновление токена """

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
            response = response.json()
            self.access_token = response['data']['attributes']['access_token']
            self.refresh_token = response['data']['attributes']['refresh_token']
            self._save_session()
        else:
            self._ssid()

    def _ssid(self):
        """ Получение SSID """

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
            response = response.json()
            self.x_ssid = response['data']['attributes']['ssid_token']
            self._jwt_auth()
        else: 
            raise Exception('Error code: {}'.format(response.status_code))

    def _jwt_auth(self):
        """ Авторизация """

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
            response = response.json()
            self.access_token = response['data']['attributes']['access_token']
            self.refresh_token = response['data']['attributes']['refresh_token']
            self._save_session()
        else: 
            raise Exception('Error code: {}'.format(response.status_code))

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
            'payment_order': '/user/payment/order'  # api.post.payment_order(currency = 'USD', purseId = 1, amount = 1000)
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
                response = self.http.get(
                    url + get_methods[method],
                    params = values
                )

            elif type == 'post':
                response = self.http.post(
                    url + post_methods[method],
                    data = values
                )

            self.last_request = time.time()

        if response.ok:
            return response.json()
        else:
            raise Exception('Error code: {}'.format(response.status_code))


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
