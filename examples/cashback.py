import epnCabinet as epn

def main():
    # Вход по данным от API
    grant_type, client_id, client_secret = ('client_credential', 'qwerty', 'asdfg')
    client = epn.init(grant_type = grant_type, client_id = client_id, client_secret = client_secret)

    try:
        client.session()
    except Exception as e:
        print(e)
        return

    api = client.api()
    
    # Получение процента кэшбэка 
    link_info = api.get.check_link(link = 'https://aliexpress.ru/item/4000581767061.html')
    cashback = link_info['data']['attributes']['cashbackPercent']
    print('Cashback: {}%'.format(cashback))



if __name__ == '__main__':
    main()