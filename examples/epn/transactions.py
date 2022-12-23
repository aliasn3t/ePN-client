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
    
    # Получение списка транзакций 
    transactions = api.get.transactions(
            tsFrom='2019-12-23', # От
            tsTo='2019-12-24', # До
            perPage=1000
        )
    
    total_revenue = 0
    total_commission_user = 0

    for transaction in transactions['data']:
        order_id = transaction['attributes']['order_number']
        revenue = transaction['attributes']['revenue']
        commission_user = transaction['attributes']['commission_user']
        date = transaction['attributes']['date']

        total_revenue += float(revenue)
        total_commission_user += float(commission_user)

        print('{}: {} ({} / {}) '.format(date, order_id, revenue, commission_user))
    print('Total revenue: {} / total commission: {}'.format(total_revenue, total_commission_user))



if __name__ == '__main__':
    main()