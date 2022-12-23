# -*- coding: utf-8 -*-

import json
import threading
import time
import requests
from requests import Request
import six
import logging
import time
import jwt


class init(object):
    request_delay = 1/3

    def __init__(self, email=None, password=None, config='aep.json'):

        self.logger = logging.getLogger()

        self.config_file = config

        self.access_token = None
        self.access_token_sign = None

        self.refresh_token = None
        self.refresh_token_sign = None

        self.x_client_id = 'web-client'

        self.user_id = None

        self.email = email
        self.password = password

        self.http = requests.Session()
        self.http.headers.update({
            'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4628.3 Safari/537.36'
        })

        self.last_request = 0.0
        self.wait = threading.Lock()

    def session(self):
        if not self.access_token:
            self._auth_token()

    def _auth_token(self):
        """ Получение токенов """

        self.logger.info('Checking config data...')
        with open(self.config_file, 'r') as config:
            cfg = json.load(config)

        if cfg['data']['access_token'] and cfg['data']['refresh_token']:
            self.access_token = cfg['data']['access_token']
            self.access_token_sign = cfg['data']['access_token_sign']
            self.refresh_token = cfg['data']['refresh_token']
            self.refresh_token_sign = cfg['data']['refresh_token_sign']
            self.user_id = cfg['data']['user_id']
            if not self._check_token():
                self._token_refresh()
        else:
            self._jwt_auth()

    def _check_token(self):
        """ Проверка токена """

        url = 'https://api.aeplatform.ru/api/v1/alerts'

        headers = {
            'x-client-id': self.x_client_id,
            'authorization': self.access_token,
            'content-type': 'application/json',
            'cookie': 'access_token={token};access_token_sign={sign}'.format(token=self.access_token, sign=self.access_token_sign)
        }

        response = self.http.get(
            url,
            headers=headers
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
        config_file = self.config_file
        with open(config_file, 'r') as config:
            cfg = json.load(config)

        cfg['data']['access_token'] = self.access_token
        cfg['data']['access_token_sign'] = self.access_token_sign
        cfg['data']['refresh_token'] = self.refresh_token
        cfg['data']['refresh_token_sign'] = self.refresh_token_sign
        cfg['data']['user_id'] = self.user_id

        with open(config_file, 'w', encoding='utf-8') as config:
            json.dump(cfg, config, ensure_ascii=False, indent=4)

    def _token_refresh(self):
        """ Обновление токена """

        self.logger.info('Refreshing...')

        url = 'https://oauth.aeplatform.ru/api/v1/refresh'

        payload = {
            "refresh_token": self.refresh_token
        }

        headers = {
            'x-client-id': self.x_client_id,
            'content-type': 'application/json',
            'cookie': 'refresh_token={token};refresh_token_sign={sign}'.format(token=self.refresh_token, sign=self.refresh_token_sign)
        }

        response = self.http.post(
            url,
            data=json.dumps(payload),
            headers=headers
        )

        if response.ok:
            self.logger.info('access_token was updated')
            response = response.cookies.get_dict()

            self.access_token = response['access_token']
            self.access_token_sign = response['access_token_sign']
            self.refresh_token = response['refresh_token']
            self.refresh_token_sign = response['refresh_token_sign']

            jwtcode = "{}.{}".format(
                response['access_token'], response['access_token_sign'])
            self.user_id = jwt.decode(
                jwtcode, options={"verify_signature": False})['user_id']

            self._save_session()
            return True
        else:
            self.logger.info('Refresh_token is not valid')
            self._jwt_auth()
            return False

    def _jwt_auth(self):
        """ Авторизация """

        self.logger.info('Auth...')

        url = 'https://oauth.aeplatform.ru/api/v1/auth'

        payload = {
            "username": self.email,
            "password": self.password
        }

        headers = {
            'x-client-id': self.x_client_id,
            'content-type': 'application/json'
        }

        response = self.http.post(
            url,
            data=json.dumps(payload),
            headers=headers
        )

        if response.ok:
            self.logger.info('Tokens received')
            response = response.cookies.get_dict()

            self.access_token = response['access_token']
            self.access_token_sign = response['access_token_sign']
            self.refresh_token = response['refresh_token']
            self.refresh_token_sign = response['refresh_token_sign']

            jwtcode = "{}.{}".format(
                response['access_token'], response['access_token_sign'])
            self.user_id = jwt.decode(
                jwtcode, options={"verify_signature": False})['user_id']

            self._save_session()
        else:
            self.logger.error('Error code: {}'.format(response.status_code))
            raise AepApiException(**response.json()["errors"][0])

    def api(self):
        return AepApiMethod(self)

    def token_expires_check(func):
        def wrapper(self, *func_args, **func_kwargs):
            try:
                return func(self, *func_args, **func_kwargs)
            except AepApiException:
                self._token_refresh()
                return func(self, *func_args, **func_kwargs)
        return wrapper

    @token_expires_check
    def method(self, params, values=None):
        """ Обработка запроса """

        query_params = params.split('.')
        type = query_params[0].lower()
        method = query_params[1].lower()

        url = 'https://api.aeplatform.ru'

        get_methods = {
            'balance': '/api/v1/users/{}/balance'.format(str(self.user_id)),            # api.get.balance()
            'user': '/api/v1/users/{}'.format(str(self.user_id)),                       # api.get.user()
            'unwrap': '/api/v1/link/unwrap',                                            # api.get.unwrap(link = https://aliclick.shop/r/c/wdsfsfsfsdfsf4435f')
            'creatives': '/api/v1/users/{}/creatives/'.format(str(self.user_id)),       # api.get.creatives()
            'placements': '/api/v1/users/{}/placements?direction=asc&order=id&page[limit]=100&page[offset]=0'.format(str(self.user_id)) # api.get.placements()
        }

        post_methods = {
            'check_link': '/api/v1/link/check',                                         # api.post.check_link(link = 'https://aliexpress.ru/item/4000581767061.html')
            'create_creative': '/api/v1/users/{}/creatives'.format(str(self.user_id)),  # api.post.create_creative(link = 'https://aliexpress.ru/item/4000581767061.html', title = "test_deeplink")
            'create_placement': '/api/v1/users/{}/placements'.format(str(self.user_id)) # api.post.create_placement(description = asdfg', type = 'personalBlog', subject = 'menFashion', aliRelation = 'direct', platform = 'telegram', theme = 'richMedia', 'link = 'https://aeplatform.ru/')
        }

        values = values.copy() if values else {}

        if self.access_token:
            self.http.headers.update({
                'x-client-id': self.x_client_id,
                'authorization': self.access_token,
                'content-type': 'application/json',
                'cookie': 'access_token={token};access_token_sign={sign}'.format(token=self.access_token, sign=self.access_token_sign)
            })

        with self.wait:
            delay = self.request_delay - (time.time() - self.last_request)

            if delay > 0:
                time.sleep(delay)

            if type == 'get':
                request = Request(method="GET", url=url +
                                  get_methods[method], params=values)
                prepared = self.http.prepare_request(request)

            elif type == 'post':
                request = Request(method="POST", url=url +
                                  post_methods[method], data=json.dumps(values))
                prepared = self.http.prepare_request(request)

            response = self.http.send(prepared)
            self.last_request = time.time()

        if response.ok:
            self.logger.info('{} request ({}) completed'.format(type, method))
            return response.json()
        elif response.status_code == 422 and method == 'create_creative':
            creative = response.json()['errors'][0]['meta']['creative_id']
            self.logger.info('Creative {} already exist!'.format(creative))
            response = self.http.get(
                url + get_methods['creatives'] + str(creative))
            if response.ok:
                return response.json()
            else:
                raise AepApiException(**response.json()["errors"][0])
        elif response.status_code == 401:
            raise AepApiException(**response.json()["errors"][0])
        else:
            self.logger.error('{} returned error code: {}'.format(
                params, response.status_code))
            raise AepApiException(**response.json()["errors"][0])


class AepApiMethod(object):
    __slots__ = ('_epn', '_method')

    def __init__(self, epn, method=None):
        self._epn = epn
        self._method = method

    def __getattr__(self, method):
        return AepApiMethod(
            self._epn, (self._method + '.' if self._method else '') + method
        )

    def __call__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            if isinstance(v, (list, tuple)):
                kwargs[k] = ','.join(str(x) for x in v)

        return self._epn.method(self._method, kwargs)


class AepApiException(Exception):
    def __init__(self, *args, **kwargs):
        self.error_code = kwargs.get('code', None)
        self.error_description = kwargs.get('error_description', None)

    def __str__(self):
        return 'Error code: {} - {}'.format(self.error_code, self.error_description)
