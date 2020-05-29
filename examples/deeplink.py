import epnCabinet as epn

def main():
    # Вход по данным от API
    grant_type, client_id, client_secret = ('client_credential', 'qwerty', 'asdfg')
    client = epn.init(grant_type, client_id, client_secret)

    try:
        client.session()
    except Exception as e:
        print(e)
        return

    api = client.api()
    
    # Cоздание диплинка
    makeDeeplink = api.post.create_creative(
            link = 'https://aliexpress.ru/item/4000581767061.html', 
            offerId = 1, # AliExpress 
            description = 'Test Deeplink', 
            type = 'deeplink'
        )
    newDeeplink = makeDeeplink['data']['attributes']['code']
    print('Deeplink: {}'.format(newDeeplink))
    

    # Сокращение полученного диплинка
    shortDomains = api.get.short_domains()
    allDomains = shortDomains['data']['attributes']

    shortDeeplink = api.post.short_link(
            urlContainer = newDeeplink,
            domainCutter = allDomains[0] # ali.pub
        )

    for link in shortDeeplink['data']['attributes']:
        print('Short deeplink: {}'.format(link['result']))



if __name__ == '__main__':
    main()