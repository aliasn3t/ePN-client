# ePN-client
Простая прослойка над API партнерской программы [epn.bz](https://epn.bz/)
В каталоге [examples](../master/examples/) есть примеры использования прослойки

#### Авторизация по данным от API
*Параметры **client_id** и **client_secret** брать по ссылке: [https://epn.bz/cabinet/#/epn-api](https://epn.bz/cabinet/#/epn-api)*
```python
import epnCabinet as epn
client = epn.init(grant_type = 'client_credential', client_id = 'qwerty', client_secret = 'asdfg')
client.session()
api = client.api()
```

#### Авторизация по логину и паролю
```python
import epnCabinet as epn
client = epn.init(login = 'user@mail.ru', password = 'passwd', check_ip = False)
client.session()
api = client.api()
```

#### GET-методы
|Метод|API URL|Пример использования|Описание|
|:---|:---|:---|:---|
|balance()|/purses/balance|api.get.**balance**()|Балансы пользователя|
|deeplinks()|/creatives/deeplinks|api.get.**deeplinks**()|Список созданных длиплинков|
|epn_stat()|/stats/overall|api.get.**epn_stat**()|Общая статистика ePN|
|user_info()|/test/user-info|api.get.**user_info**()|Информация о пользователе|
|transactions()|/transactions/user|api.get.**transactions**(tsFrom = '2019-12-23', tsTo = '2019-12-24', perPage = 1000)|Список транзакций|
|check_link()|/affiliate/checkLink|api.get.**check_link**(link = 'https://aliexpress.ru/item/4000581767061.html')|Проверка URL|
|short_domains()|/link-reduction/domain-cutter-list|api.get.**short_domains**()|Список доступных доменов для сокращения ссылок|
|payments()|/user/payment/init|api.get.**payments**()|Информация по выплатам, кошелькам, комиссиям|
|purses()|/user/purses/list|api.get.**purses**()|Список кошельков пользователя|

#### POST-методы
|Метод|API URL|Пример использования|Описание|
|:---|:---|:---|:---|
|create_creative()|/creative/create|api.post.**create_creative**(link = 'https://aliexpress.ru/item/4000581767061.html', offerId = 1, description = 'test_deeplink', type = 'deeplink')|Создание реферальной ссылки|
|short_link()|/link-reduction|api.post.**short_link**(urlContainer = 'https://aliexpress.ru/item/4000581767061.html', domainCutter = 'ali.pub')|Сокращение реферальной ссылки|
|payment_order()|/user/payment/order|api.post.**payment_order**(currency = 'USD', purseId = 1, amount = 1000)|Заказ выплаты|
|logout_client_id()|/logout|api.post.**logout_client_id**(client_id = 'asdfg')|Деактивация всех refresh_token для client_id|
|logout_refresh_token()|/logout/refresh-token|api.post.**logout_refresh_token**(refresh_token = 'asdfg', client_id = 'asdfg')|Деактивация refresh_token|
|logout_all()|/logout/all|api.post.**logout_all**(client_id = 'asdfg')| Деактивация всех токенов пользователя|
