import epnCabinet as epn

def main():
    # Вход по логину и паролю
    login, password, check_ip = ('user@mail.ru', 'password', False)
    client = epn.init(username = login, password = password, check_ip = check_ip)

    try:
        client.session()
    except Exception as e:
        print(e)
        return

    api = client.api()
    
    # Получение информации о текущем балансе аккаунта
    balance = api.get.balance()

    for id in balance['data']:
        if id['attributes']['existBalance']:
            currency = id['id']
            available_amount = id['attributes']['availableAmount']
            hold_amount = id['attributes']['holdAmount']
            all_money = id['attributes']['allMoney']
            summary_payments = id['attributes']['summaryPayments']

            print('Balance {}: All - {} / Available amount - {} / Hold - {} / Summary payments - {}'.format(currency, all_money, available_amount, hold_amount, summary_payments))



if __name__ == '__main__':
    main()