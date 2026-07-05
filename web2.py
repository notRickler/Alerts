from telethon.sync import TelegramClient
from datetime import datetime
from bs4 import BeautifulSoup as Bs
import requests
import json
import time
import random
import configparser
import re

# Данные Telegram API вынесены в переменные, чтобы не хранить личные значения внутри TelegramClient.
api_id = 123456
api_hash = 'your_api_hash'

# Кому в Telegram отправлять служебные уведомления о запуске и ошибках.
# Можно указать как канал, так и пользователя, без @
ADMIN_CHAT = 'username'

# Канал Telegram, куда публикуются готовые алерты о листингах.
# Можно указать как канал, так и пользователя, без @
ALERTS_CHANNEL = 'channel_username'

launch_errors = 0
last_id = 0
bithumb1 = 0
bithumb2 = 0
link_result = ""
nokx_latest = []
jump_latest = []
mexc_latest = None
huobi_latest = "" 
binance_latest = ""
kraken_latest = ""
proxy = []
# static_prx используется только там, где нужен один фиксированный proxy.
# prx ниже меняется через proxySet() и используется для обычной ротации proxy из proxyS.txt.
static_prx = 'socks5://login:password@ip:port'
prx = ''
build = ''
bitscore = 0
# Загружаем список proxy для запросов к сайтам бирж.
# Каждый вызов proxySet() выбирает случайный proxy из этого списка.
file = open('proxyS.txt', 'r')

while True:
    line = file.readline()
    if not line:break
    proxy.append(line.strip())

file.close

def times():
    return datetime.now().strftime('%d.%m [%H:%M:%S.%f')[:-3]+str('] ')

def log(text):
    with open('logsWeb.txt', 'a', encoding="utf-8") as f_in:
        f_in.write(str('\n')+times()+' '+text)
    print(times(),text)

def proxySet():
    # Меняет глобальный proxy для следующего круга запросов.
    global prx
    prx = proxy[random.randint(0,len(proxy)-1)]

def ticker_improve(tick):
    # Для коротких тикеров используется $TICKER, для длинных/цифровых — #TICKER.
    if any(char.isdigit() for char in tick) or len(tick)>8:res = str('''#''')+str(tick)
    else:res = str('$')+str(tick)
    res = res.upper()
    return res

def launch_bithumb(): #отдельный модуль запуска bithumb, нужен из-за периодически обновляющегося buildId у сайта, без которого api не работает
    # У Bithumb API зависит от buildId сайта, поэтому сначала парсим HTML, а потом делаем API-запросы.
    global bithumb1,bithumb2,build
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
              'Accept-Encoding':'gzip, deflate, br',
                'Accept-Language':'en-US,en;q=0.9',
                'Cache-Control':'no-cache',
                'Dnt':'1',
                'Pragma':'no-cache',
                'Sec-Ch-Ua':'''"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"''',
                'Sec-Ch-Ua-Mobile':'?0',
                'Sec-Ch-Ua-Platform':'''"Windows"''',
              }
    for t in range(5):
        try:
            log(str('bithumb loop'+str(t)))
            t = t + 1
            bhurl='https://feed.bithumb.com/notice?category=8&page=1'
            html = requests.get(bhurl, headers = header, proxies=dict(https=static_prx), timeout=13).text 
            soup = Bs(html,'html.parser')
            print(soup)
            soup = str(soup)
            log(str(soup))
            x = soup.find("buildId") #парсим номер билда с сайта для дальнейших запросов по api
            log(str(x))
            build = soup[x+10:x+31]
            log(str(build))
            response1 = json.loads(requests.get(f'https://feed.bithumb.com/_next/data/{build}/notice.json?category=8&keyword=&page=1', headers = header, proxies=dict(https=static_prx), timeout=27).text) 
            log(str(response1))
            bithumb1 = response1["pageProps"]["noticeList"][0]["id"]
            response2 = json.loads(requests.get(f'https://feed.bithumb.com/_next/data/{build}/notice.json?category=9&keyword=&page=1', headers = header, proxies=dict(https=static_prx), timeout=27).text) 
            bithumb2 = response2["pageProps"]["noticeList"][0]["id"]
            break
        except Exception:
            log(str('bithumb launch err'+str(t)))
            time.sleep(2)
            continue

def start():
    # При запуске запоминаем последние известные новости, чтобы не отправлять старые листинги.
    global prx,url,last_id,link_result,nokx_latest,huobi_latest,binance_latest,kraken_latest,jump_latest
    log('launching...')
    #Upbit
    url = "https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=20&category=trade" #"https://api-manager.upbit.com/api/v1/notices?page=1&per_page=20&thread_name=general"
    response = json.loads(requests.get(url, proxies=dict(https=prx), timeout=27).text)
    last_id = response["data"]["notices"][0]["id"]
    print("upbit latest: ",response["data"]["notices"][0]["title"])
    #Bitfinex
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
              'Accept-Encoding':'gzip, deflate, br',
                'Accept-Language':'en-US,en;q=0.9',
                'Cache-Control':'no-cache',
                'Dnt':'1',
                'Pragma':'no-cache',
                'Sec-Ch-Ua':'''"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"''',
                'Sec-Ch-Ua-Mobile':'?0',
                'Sec-Ch-Ua-Platform':'''"Windows"''',
              } 
    burl = 'https://blog.bitfinex.com/category/media-releases/'
    html = requests.get(burl, headers = header, proxies=dict(https=static_prx), timeout=27).text
    soup = Bs(html, 'html.parser')
    result = soup.find_all('a', attrs={'itemprop': 'url'})[1] #list index out of range
    link_result = result.get('href')
    #newOKX
    nourl = "https://www.okx.com/v2/support/home/web"
    response = json.loads(requests.get(nourl, proxies=dict(https=prx), timeout=27).text)
    nokx_latest = response["data"]["notices"]
    response = json.loads(requests.get('https://www.okx.com/api/v3/jumpstart/projects', proxies=dict(https=prx), timeout=27).text)
    jump_latest = []
    try:
        jump_latest = response["data"]["upcomingList"][0]["currencyShortName"]
    except Exception: jump_latest = []
    try:
        if(len(jump_latest)==0):
            jump_latest = response["data"]["ongoingList"][0]["currencyShortName"]
    except Exception:jump_latest = []
    #Huobi
    try:
        hurl='https://www.htx.com/-/x/support/public/getList/v2?language=en-us&page=1&limit=20&oneLevelId=360000031902&twoLevelId=360000039942'
        response = json.loads(requests.get(hurl, proxies=dict(https=prx), timeout=27).text)
        huobi_latest = response["data"]["list"][0]["title"]
    except Exception:log(' huobi launch err')
    #Binance
    try:
        binurl = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query?type=1&pageNo=1&pageSize=10"
        response = json.loads(requests.get(binurl, proxies=dict(https=prx), timeout=27).text)
        binance_latest = response["data"]["catalogs"][0]["articles"][0]["title"]
    except Exception:log(' binance launch err')
    '''
    binurl='https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48' #'https://www.binance.com/en/support/announcement' #
    html = requests.get(binurl, proxies=dict(https=prx)).text
    soup = Bs(html,'html.parser')
    try:
        last_article = soup.find_all('script')[11].text
        response = json.loads(last_article)
    except Exception:
        for o in range(13,8,-1):
            try:
                last_article = soup.find_all('script')[o].text
                response = json.loads(last_article)
                break
            except Exception:continue
    #print(last_article)
    binance_latest = response["appState"]["loader"]["dataByRouteId"]["2a3f"]["catalogs"][0]["articles"][0]["title"]'''
    #Kraken
    kurl = 'https://blog.kraken.com/category/product/asset-listings' #https://blog.kraken.com/category/product/asset-listings
    html = requests.get(kurl, proxies=dict(https=prx), timeout=27).text
    soup = Bs(html, 'html.parser')
    kraken_latest = soup.find_all('h2', attrs={'class': 'title'})[0].text
    #Bithumb - там все сломалось
    #launch_bithumb() +'\n'+str(bithumb1)+'\n'+str(bithumb2)
    launch = str(str(last_id)+'\n'+str(link_result)+'\n'+str(nokx_latest)+'\n'+str(jump_latest)+'\n'+str(huobi_latest)+'\n'+str(binance_latest)+'\n'+str(kraken_latest))
    log(launch)
    log('Started!')
    #time.sleep(1000) #temporary

def duplicate_check(ex,ticker): #проверка на дубли по названию биржи и тикеру, биржи часто выпускают несколько новостей по 1 листингу, нам это не нужно
    # Если пара биржа+тикер уже была в duplicates.txt, повторно сообщение не отправляем.
    # При новом листинге сразу увеличиваем недельный счётчик в data.ini.
    match=0
    ticker=ticker.upper()
    duplicates = []
    file = open('duplicates.txt', 'r', encoding="utf-8")
    while True:
        line = file.readline()
        if not line:break
        duplicates.append(line.strip())
    file.close
    for i in range(len(duplicates)-1):
        if(duplicates[i]==ex and duplicates[i+1]==ticker):match=1
    if(ticker=='BTC' or ticker=='ETH' or ticker=='USD' or ticker=='OTC' or ticker=='EUR' or ticker=='USDT' or ticker=='NFT' or ticker=='USDC' or ticker=='UTC' or ticker=='AM' or ticker=='PM' or ticker.isdigit()==True):match=1
    if(match>0):return True
    else:
        duplicates.append(ex)
        duplicates.append(ticker)
        with open('duplicates.txt', 'a', encoding="utf-8") as f_in:
            f_in.write(str('\n')+ex)
        with open('duplicates.txt', 'a', encoding="utf-8") as f_in:
            f_in.write(str('\n')+ticker)
        log(str(ticker)+str(ex)+str(' added'))
        config = configparser.ConfigParser(strict=False)
        config.read("data.ini")
        if(ex=="binlist"):config['Listings']['binance']=str(int(config['Listings']['binance'])+1)
        if(ex=="binallist"):config['Listings']['binance']=str(int(config['Listings']['binance'])+1)
        if(ex=="upbit"):config['Listings']['upbit']=str(int(config['Listings']['upbit'])+1)
        if(ex=="bitfinex"):config['Listings']['bitfinex']=str(int(config['Listings']['bitfinex'])+1)
        if(ex=="huobi"):config['Listings']['htx']=str(int(config['Listings']['htx'])+1)
        if(ex=="okx"):config['Listings']['okx']=str(int(config['Listings']['okx'])+1)
        if(ex=="kraken"):config['Listings']['kraken']=str(int(config['Listings']['kraken'])+1)
        if(ex=="bithumb"):config['Listings']['bithumb']=str(int(config['Listings']['bithumb'])+1)
        if(ex=="mexc"):config['Listings']['mexc']=str(int(config['Listings']['mexc'])+1)
        with open('data.ini', 'w') as config_file:
            config.write(config_file)
        return False

# Ниже идут отдельные проверки для каждой биржи.
# Каждая функция получает свежую новость, сравнивает её с сохранённой последней новостью и отправляет сообщение только при обновлении.
def check_upbit():
    global prx,url,last_id
    response = json.loads(requests.get(url, proxies=dict(https=prx), timeout=27).text)
    current_id = response["data"]["notices"][0]["id"]
    log(str(current_id))
    #last_id = 3777
    #current_id = 3797
    #print(current_id)
    if (last_id < current_id):
        log('Upbit finded')
        last_id = current_id
        data = response["data"]["notices"][0]["title"]
        #data = '[거래] KRW 마켓 디지털 자산 추가 (MSK)'
        #data = '거래 KRW, BTC 마켓 디지털 자산 추가 (SXL, MTTIC)'
        if (data.lower().find('krw') >= 0 or data.lower().find('btc') >= 0 or data.lower().find('usdt') >= 0):
            tickers = data.split()
            words = []
            del_index = []
            final=''
            added = 0
            krw = False
            btc = False
            regex = re.compile('[^a-zA-Z0-9]')
            for line in tickers: words += [w for w in line.split() if w.isupper()]  # ищем слово КАПСОМ
            for d in range(len(words)):
                words[d] = "".join(c for c in words[d] if c.isalnum())
                words[d] = regex.sub('', words[d])
            for x in range(len(words)):  # удаляем лишние тикеры
                if (words[x].find('KRW') > -1):
                    del_index = [x] + del_index
                    krw = True
                if (words[x].find('BTC') > -1):
                    del_index = [x] + del_index
                    btc = True
                if (words[x].find('USDT') > -1):
                    del_index = [x] + del_index
                    btc = True
            for z in range(len(del_index)):  # удаляем лишние тикеры
                words.pop(del_index[z])
            pair_ticker = ''
            if (len(words) == 1):
                ticker = words[0]
                if(krw == True):pair_ticker='KRW'
                if(btc == True):pair_ticker='BTC'
                if(duplicate_check('upbit',words[0]+pair_ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥 Upbit lists " + tag + " ([link](https://upbit.com/service_center/notice?id=" + str(
                        last_id) + ") / [pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) +"-" + str(
                        ticker.upper()) + "))\n\n@rickler_alerts"
                    added += 1
                else:log('Upbit duplicate')
            elif (len(words) > 1):
                final = "🔥🔥🔥 Upbit lists "+str(len(words))+" tokens ([link](https://upbit.com/service_center/notice?id="+str(last_id)+')):\n\n'
                if (krw == True and btc == False):
                    pair_ticker = 'KRW'
                    for h in range(len(words)):
                        if(duplicate_check('upbit',words[h]+pair_ticker) == False):
                            tag = ticker_improve(words[h])
                            final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) +"-" + str(words[h].upper()) + "))\n"
                            added += 1
                        else:log('Upbit duplicate')
                if (btc == True and krw == False):
                    pair_ticker = 'BTC'
                    for h in range(len(words)):
                        if(duplicate_check('upbit',words[h]+pair_ticker) == False):
                            tag = ticker_improve(words[h])
                            final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) + "-" + str(words[h].upper()) + "))\n"
                            added += 1
                        else:log('Upbit duplicate')
                if (krw == True and btc == True):
                    pair_ticker = 'KRW'
                    if(duplicate_check('upbit',words[0]+pair_ticker) == False):
                        tag = ticker_improve(words[0])
                        final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) + "-" + str(words[0].upper()) + "))\n"
                        added += 1
                    else:log('Upbit duplicate')
                    pair_ticker = 'BTC'
                    for h in range(1,len(words)):
                        if(duplicate_check('upbit',words[h]+pair_ticker) == False):
                            tag = ticker_improve(words[h])
                            final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) + "-" + str(words[h].upper()) + "))\n"
                            added += 1
                        else:log('Upbit duplicate')
                final = final + "\n@rickler_alerts"
            if(len(final)>0 and added > 0):
                with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                    client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                    client.disconnect()
            else:log('Upbit IFELSE error or duplicate')
        else:log(' Upbit filtered!')

def check_bitfinex():
    global prx,link_result,bitscore
    bitscore += 1
    if (bitscore%100!=0): return log(str(bitscore)) #задержка парсинга 1 раз в 100 итераций для избежания блокировки из-за частых запросов
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
              'Accept-Encoding':'gzip, deflate, br',
                'Accept-Language':'en-US,en;q=0.9',
                'Cache-Control':'no-cache',
                'Dnt':'1',
                'Pragma':'no-cache',
                'Sec-Ch-Ua':'''"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"''',
                'Sec-Ch-Ua-Mobile':'?0',
                'Sec-Ch-Ua-Platform':'''"Windows"''',
              } 
    burl='https://blog.bitfinex.com/category/media-releases/'
    html = requests.get(burl, headers = header, proxies=dict(https=static_prx), timeout=27).text
    soup = Bs(html,'html.parser')
    result2 = soup.find_all('a', attrs={'itemprop':'url'})[1]
    #ссылка на конкретную новость вместо крайней, для проверки работы парсинга
    #result2 = 'https://blog.bitfinex.com/media-releases/strongbitfinex-to-list-innovative-defi-forex-hub-onomy-protocol-nomnbsp-strong/'
    titlez = result2.get('title')
    result2 = result2.get('href')
    log(titlez)
    log(result2)
    if(result2!=link_result):
        log('Bitfinex finded')
        if(titlez.lower().find('bitfinex derivatives')==-1 and titlez.lower().find('derivatives')==-1):
            if(titlez.lower().find('will list')>-1 or
            titlez.lower().find('will be listing')>-1 or
            titlez.lower().find('to list')>-1):
                del_index = []
                tickers = titlez.split()
                words = []
                for line in tickers: words += [w for w in line.split() if w.startswith('(')]
                for line in tickers: words += [w for w in line.split() if w.isupper()]
                for x in range(len(words)):  # удаляем лишние тикеры
                    if (words[x].find('NFT') > -1):del_index = [x] + del_index
                    if (words[x].find('UTC') > -1):del_index = [x] + del_index
                    if (words[x].find('DEX') > -1):del_index = [x] + del_index
                    if (words[x].find('EVM') > -1):del_index = [x] + del_index
                for z in range(len(del_index)):  # удаляем лишние тикеры
                    words.pop(del_index[z])
                if(len(words)>0): ticker = words[len(words)-1]
                else: ticker = tickers[-1]
                ticker = "".join(c for c in ticker if c.isalnum()).upper()
                if(duplicate_check('bitfinex',ticker.upper()) == False):
                    tag = ticker_improve(ticker)
                    final = "Bitfinex lists " + tag + " ([link](" + str(result2) + ") / [pair](https://trading.bitfinex.com/t/" + str(ticker) + ":UST))\n\n@rickler_alerts"
                    with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                        client.send_message(ALERTS_CHANNEL, final, link_preview=False, silent=True)
                        client.disconnect()
                else:log('Bitfinex duplicate')
            else:log('Bitfinex filtered')
        link_result = result2

def check_htx():
    global prx,huobi_latest
    hurl = 'https://www.htx.com/-/x/support/public/getList/v2?language=en-us&page=1&limit=20&oneLevelId=360000031902&twoLevelId=360000039942'
    response = json.loads(requests.get(hurl, proxies=dict(https=prx), timeout=27).text)
    last_article = response["data"]["list"][0]["title"]
    log(last_article)
    hype = response["data"]["list"][0]["id"]
    hyperlink = str('https://www.htx.com/support/')+str(hype)
    if(huobi_latest!=last_article):
        log('HTX finded')
        huobi_latest=last_article
        data = last_article
        if(data.lower().find('will list') >= 0 or data.lower().find('will open') >= 0 or data.lower().find('open trading') >= 0):
            tickers = last_article.split()
            words = []
            del_index = []
            for line in tickers: words += [w for w in line.split() if w.isupper()]
            for x in range(len(words)):  # удаляем лишние тикеры
                if (words[x].find('UTC') > -1):del_index = [x] + del_index
                if (words[x].find('HTX') > -1):del_index = [x] + del_index
                if (words[x].find('(') > -1 or words[x].find(')') > -1):del_index = [x] + del_index
            for z in range(len(del_index)):  # удаляем лишние тикеры
                words.pop(del_index[z])
            if(len(words)==0 and duplicate_check('huobi',hyperlink) == False): # 
                ticker = 'TickerParseErr0r'
                final = "HTX lists $" + ticker + " ([link](" + str(hyperlink) + "?invite_code=iyq3b) / [pair](https://www.htx.com/trade/btc_usdt?invite_code=iyq3b))\n\n@rickler_alerts"
            elif (len(words) == 1 and duplicate_check('huobi',words[0]) == False):
                ticker = words[0]
                tag = ticker_improve(ticker)
                final = "HTX lists " + tag + " ([link](" + str(hyperlink) + "?invite_code=iyq3b) / [pair](https://www.htx.com/trade/"+str(ticker.lower())+"_usdt?invite_code=iyq3b))\n\n@rickler_alerts"
            elif (len(words) > 1 and duplicate_check('huobi',words[0]) == False and duplicate_check('huobi',words[1]) == False):
                final = "HTX lists "+str(len(words))+" tokens ([link]("+str(hyperlink)+'?invite_code=iyq3b)):\n\n'
                for h in range(len(words)):
                    tag = ticker_improve(words[h])
                    final = final + tag + " ([pair](https://www.htx.com/trade/"+str(words[h].lower())+"_usdt?invite_code=iyq3b))\n"
                final = final + "\n@rickler_alerts"
            with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                client.disconnect()
        else:log('HTX filtered')

def check_binance():
    global prx,binance_latest
    binurl = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query?type=1&pageNo=1&pageSize=10"
    response = json.loads(requests.get(binurl, proxies=dict(https=prx), timeout=27).text)
    last_ann = response["data"]["catalogs"][0]["articles"][0]["title"]
    last_code = response["data"]["catalogs"][0]["articles"][0]["code"]
    log(last_ann)
    #заголовки для теста 
    #last_ann = 'Binance Will List Terra 2.0 (LUNA) in the Innovation Zone *LUNA (old) Renamed as LUNC'
    #last_ann = 'Introducing the Open Campus (EDU) Token Sale on Binance Launchpad!'
    #last_ann = 'Introducing Radiant Capital (RDNT) on Binance Launchpool! Farm RDNT by Staking BNB and TUSD'
    #print(last_ann,last_code)
    if(binance_latest!=last_ann):
        binance_latest = last_ann
        data = last_ann
        log('binance finded')
        hyperlink = str('https://www.binance.com/en/support/announcement/')+str(last_code)
        if((data.lower().find('will list') >= 0 and data.lower().find('options')==-1 and data.lower().find('margin')==-1 and data.lower().find('futures')==-1) or (data.lower().find('hodler') >= 0)):
            tickers = last_ann.split()
            words = []
            del_index = []
            for line in tickers: words += [w for w in line.split() if w.startswith('(')]
            for x in range(len(words)):  # удаляем лишние тикеры
                if (words[x].find('old') > -1):del_index = [x] + del_index
            for z in range(len(del_index)):  # удаляем лишние тикеры
                words.pop(del_index[z])
            for d in range(len(words)):
                    words[d] = "".join(c for c in words[d] if c.isalnum())
            if(len(words) > 0):ticker = words[0]
            else:
                for line in tickers: words += [w for w in line.split() if w.isupper()]
                if(len(words) > 0):
                    ticker = words[0]
                    tag = ticker_improve(ticker)
                    if(duplicate_check('binlist',ticker) == False):final = "🔥 Binance lists " + tag + " ([link](" + str(hyperlink) + ") / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                elif(duplicate_check('binlist','Error') == False):final = "🔥 Binance lists $TickerError ([link](" + str(hyperlink) + "?ref=JAO4CT0D))\n\n@rickler_alerts"
            if (len(words) == 1 and duplicate_check('binlist',ticker) == False):
                tag = ticker_improve(ticker)
                final = "🔥 Binance lists " + tag + " ([link](" + str(hyperlink) + ") / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
            elif (len(words) > 1 and duplicate_check('binlist',ticker) == False):
                final = "🔥🔥🔥 Binance lists "+str(len(words))+" tokens ([link]("+str(hyperlink)+'?ref=JAO4CT0D)):\n\n'
                for h in range(len(words)):
                    tag = ticker_improve(words[h])
                    final = final + tag + " ([pair](https://www.binance.com/en/trade/"+str(words[h].upper())+"_USDT?ref=JAO4CT0D))\n"
                final = final + "\n@rickler_alerts"
            with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                client.disconnect()
        elif(data.lower().find('binance alpha') >= 0):
            tickers = msg.split()
            words = []
            del_index = []
            for line in tickers: words += [w for w in line.split() if w.startswith('(')]
            if(len(words) > 0):
                ticker = words[0]
                tag = ticker_improve(ticker)
                if(duplicate_check('binallist',ticker) == False):
                    final = "🔥 Binance Alpha lists " + tag + " ([link](" + str(hyperlink) + "?ref=JAO4CT0D))\n\n@rickler_alerts"
                    client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                    client.disconnect()
        elif(data.lower().find('introducing') >= 0 and data.lower().find('on binance')>=0):
            tickers = last_ann.split()
            words = []
            for line in tickers: words += [w for w in line.split() if w.startswith('(')]
            for d in range(len(words)):
                    words[d] = "".join(c for c in words[d] if c.isalnum())
            ticker = words[0]
            for d in range(len(words)):
                    words[d] = "".join(c for c in words[d] if c.isalnum())
            tag = ticker_improve(ticker)
            if(data.lower().find('megadrop') >= 0 and duplicate_check('binlist',ticker) == False):
                final = "🔥🔥🔥 Binance announced " + tag + " Megadrop! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
            if(data.lower().find('launchpad') >= 0 and duplicate_check('binlist',ticker) == False):
                final = "🔥🔥🔥 Binance announced " + tag + " token sale! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
            if(data.lower().find('launchpool') >= 0 and duplicate_check('binlist',ticker) == False):
                final = "🔥🔥🔥 Binance announced " + tag + " farm! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
            with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                client.disconnect() 
        else:log('Binance filtered')

def check_okx():
    global prx,nokx_latest,jump_latest
    nourl = "https://www.okx.com/v2/support/home/web"
    response = json.loads(requests.get(nourl, proxies=dict(https=prx), timeout=27).text)
    log(response["data"]["notices"][0]["link"])
    last_article = response["data"]["notices"]
    #заголовок для теста last_article[0]["shareTitle"]="OKX to list MAJOR (Maxar) for spot trading"
    req = json.loads(requests.get('https://www.okx.com/api/v3/jumpstart/projects', proxies=dict(https=prx), timeout=27).text)
    last_jump = []
    try:
        last_jump = req["data"]["upcomingList"][0]["currencyShortName"]
        if(jump_latest!=last_jump):
            log('OKX Jump 1 finded')
            ticker = last_jump
            hyperlink = 'https://www.okx.com/jumpstart/project/' + str(req["data"]["upcomingList"][0]["projectId"])
            if(duplicate_check('okx',ticker) == False):
                tag = ticker_improve(ticker)
                final = "🔥 OKX announced " + tag + " token sale! ([link](" + str(hyperlink) + "?channelId=RICKLER) / [pair](https://www.okx.com/trade-spot/"+str(ticker.lower())+"-usdt?channelId=RICKLER))\n\n@rickler_alerts"
                with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                    client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                    client.disconnect()
            else:log('OKX Jump duplicate')
            jump_latest = last_jump
    except Exception: last_jump = []
    try:
        if(len(last_jump)==0):
            last_jump = req["data"]["ongoingList"][0]["currencyShortName"]
            if(jump_latest!=last_jump):
                log('OKX Jump 2 finded')
                ticker = last_jump
                hyperlink = 'https://www.okx.com/jumpstart/project/' + str(req["data"]["ongoingList"][0]["projectId"])
                if(duplicate_check('okx',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥 OKX announced " + tag + " token sale! ([link](" + str(hyperlink) + "?channelId=RICKLER) / [pair](https://www.okx.com/trade-spot/"+str(ticker.lower())+"-usdt?channelId=RICKLER))\n\n@rickler_alerts"
                    with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                        client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                        client.disconnect()
                else:log('OKX Jump duplicate')
                jump_latest = last_jump
    except Exception:last_jump = []
    if(nokx_latest!=last_article):
        log('nOKX finded')
        for h in range(len(last_article)-17):
            if(last_article[h]["shareTitle"]!=nokx_latest[h]["shareTitle"]):
                hpx = response["data"]["notices"][h]["link"]
                data = response["data"]["notices"][h]["shareTitle"]
                #заголовок для теста data = "OKX to list MAJOR (Maxar) for spot trading"
                hyperlink = str('https://www.okx.com')+str(hpx)
                if((data.lower().find('introducing') >= 0 and data.lower().find('jumpstart') >= 0) or (data.lower().find('jumpstart') >= 0 and data.lower().find('sale details') >= 0) or (data.lower().find('jumpstart') >= 0 and data.lower().find('stake okb') >= 0) or (data.lower().find('jumpstart') >= 0 and data.lower().find('about') >= 0)):
                    tickers = data.split()
                    words = []
                    del_index = []
                    for line in tickers: words += [w for w in line.split() if w.isupper()]
                    for d in range(len(words)):
                        words[d] = "".join(c for c in words[d] if c.isalnum())
                    for x in range(len(words)):  # удаляем лишние тикеры
                        if (words[x] == 'OKX'):del_index = [x] + del_index
                        if (words[x] == 'AI'):del_index = [x] + del_index
                        if (words[x] == 'DAO'):del_index = [x] + del_index
                        if (words[x] == 'NFT'):del_index = [x] + del_index
                    for z in range(len(del_index)):  # удаляем лишние тикеры
                        words.pop(del_index[z])
                    ticker = words[0]
                    if(duplicate_check('okx',ticker) == False):
                        tag = ticker_improve(ticker)
                        final = "🔥 OKX announced " + tag + " token sale! ([link](" + str(hyperlink) + "?channelId=RICKLER) / [pair](https://www.okx.com/trade-spot/"+str(ticker.lower())+"-usdt?channelId=RICKLER))\n\n@rickler_alerts"
                        with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                            client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                            client.disconnect()
                    else:log('okx 1 duplicate')
                if((data.lower().find('will list') >= 0 and data.lower().find('spot') >= 0 and data.lower().find('/') == -1) or (data.lower().find('to list') >= 0 and data.lower().find('spot') >= 0 and data.lower().find('/') == -1) or (data.lower().find('lists') >= 0 and data.lower().find('spot') >= 0 and data.lower().find('/') == -1)):
                    forParse = data.split()
                    tickers = []
                    words = []
                    del_index = []
                    checker = False
                    for k in range(len(forParse)):
                        if(forParse[k].startswith('(')):
                            checker = True
                            break
                        else:words.append(forParse[k])
                    if(checker):
                        ticker = ""
                        ticker = words[len(words)-1]
                        log(ticker)
                        if(len(ticker) > 0 and duplicate_check('okx',ticker) == False):
                            tag = ticker_improve(ticker)
                            final = "🔥 OKX lists " + tag + " ([link](" + str(hyperlink) + "?channelId=RICKLER) / [pair](https://www.okx.com/trade-spot/"+str(ticker.lower())+"-usdt?channelId=RICKLER))\n\n@rickler_alerts"
                            with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                                client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                                client.disconnect()
                        else:log('nokx 2 duplicate')
                    else:
                        words = []
                        for line in forParse: words += [w for w in line.split() if w.isupper()]
                        for x in range(len(words)):  # удаляем лишние тикеры
                            if (words[x] == 'OKX'):del_index = [x] + del_index
                            if (words[x] == 'AI'):del_index = [x] + del_index
                            if (words[x] == 'DAO'):del_index = [x] + del_index
                            if (words[x] == 'NFT'):del_index = [x] + del_index
                            if (words[x].lower().find('(') != -1):del_index = [x] + del_index
                            if (words[x].lower().find(')') != -1):del_index = [x] + del_index
                        for d in range(len(words)):
                            words[d] = "".join(c for c in words[d] if c.isalnum())
                        for z in range(len(del_index)):  # удаляем лишние тикеры
                            words.pop(del_index[z])
                        if(len(words) == 1):
                            ticker = words[0]
                            log(ticker)
                            if(duplicate_check('okx',ticker) == False):
                                tag = ticker_improve(ticker)
                                final = "🔥 OKX lists " + tag + " ([link](" + str(hyperlink) + "?channelId=RICKLER) / [pair](https://www.okx.com/trade-spot/"+str(ticker.lower())+"-usdt?channelId=RICKLER))\n\n@rickler_alerts"
                                with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                                    client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                                    client.disconnect()
                        elif(len(words) > 1 and duplicate_check('okx',words[0]) == False):
                            final = "🔥🔥🔥 OKX lists "+str(len(words))+" tokens ([link]("+str(hyperlink)+'?channelId=RICKLER)):\n\n'
                            for h in range(len(words)):
                                tag = ticker_improve(words[h])
                                final = final + tag + " ([pair](https://www.okx.com/trade-spot/"+str(words[h].lower())+"-usdt?channelId=RICKLER))\n"
                            final = final + "\n@rickler_alerts"
                            with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                                client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                                client.disconnect()
                        else:log('nOKX ticker detect error')
        nokx_latest=last_article

def check_kraken():
    global prx,kraken_latest
    kurl = 'https://blog.kraken.com/category/product/asset-listings'
    html = requests.get(kurl, proxies=dict(https=prx), timeout=27).text
    soup = Bs(html, 'html.parser')
    result2 = soup.find_all('h2', attrs={'class': 'title'})[0]
    hrefer=(result2.a.get('href'))
    result2 = soup.find_all('h2', attrs={'class': 'title'})[0].text
    log(result2)
    if(result2!=kraken_latest):
        log('Kraken finded')
        kraken_latest = result2
        if(result2.lower().find('trading for')>-1 or result2.lower().find('for trading')>-1):
            del_index = []
            tickers = result2.split()
            words = []
            for line in tickers: words += [w for w in line.split() if w.startswith('(')]
            for d in range(len(words)):
                    words[d] = "".join(c for c in words[d] if c.isalnum())
            for x in range(len(words)):  # удаляем лишние тикеры
                if (words[x].find('NFT') > -1):del_index = [x] + del_index
                if (words[x] == 'USA'):del_index = [x] + del_index
                if (words[x] == 'CA'):del_index = [x] + del_index
                if (words[x] == 'BY'):del_index = [x] + del_index
                if (words[x].lower().find('kraken') > -1):del_index = [x] + del_index
                if (words[x].find('EVM') > -1):del_index = [x] + del_index
            for z in range(len(del_index)):  # удаляем лишние тикеры
                words.pop(del_index[z])
            if(len(words)==1):
                ticker=words[0]
                if(duplicate_check('kraken',ticker.upper()) == False):
                    tag = ticker_improve(ticker)
                    final = "Kraken lists " + tag + " ([link](" + str(hrefer) + ") / [pair](https://pro.kraken.com/app/trade/" + str(ticker.lower()) + "-usd))\n\n@rickler_alerts"
                    with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                        client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                        client.disconnect()
                else:log('Kraken duplicate')
            else:
                del_index = []
                tickers = result2.split()
                words = []
                for line in tickers: words += [w for w in line.split() if w.isupper()]
                for d in range(len(words)):
                        words[d] = "".join(c for c in words[d] if c.isalnum())
                for x in range(len(words)):  # удаляем лишние тикеры
                    if (words[x].find('NFT') > -1):del_index = [x] + del_index
                    if (words[x] == 'USA'):del_index = [x] + del_index
                    if (words[x] == 'CA'):del_index = [x] + del_index
                    if (words[x] == 'BY'):del_index = [x] + del_index
                    if (words[x].lower().find('kraken') > -1):del_index = [x] + del_index
                    if (words[x].find('EVM') > -1):del_index = [x] + del_index
                for z in range(len(del_index)):  # удаляем лишние тикеры
                    words.pop(del_index[z])
                if(len(words)==0 and duplicate_check('kraken',hyperlink) == False):
                    tickers = result2.split()
                    ticker = tickers[0]
                    if(duplicate_check('kraken',ticker.upper()) == False):
                        final = "Kraken lists $" + ticker.upper() + " ([link](" + str(hrefer) + ") / [pair](https://pro.kraken.com/app/trade/" + str(ticker.lower()) + "-usd))\n\n@rickler_alerts"
                        with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                            client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                            client.disconnect()
                    else:log('Kraken no ticker')
                elif(len(words)==1):
                    ticker=words[0]
                    if(duplicate_check('kraken',ticker.upper()) == False):
                        tag = ticker_improve(ticker)
                        final = "Kraken lists " + tag + " ([link](" + str(hrefer) + ") / [pair](https://pro.kraken.com/app/trade/" + str(ticker.lower()) + "-usd))\n\n@rickler_alerts"
                        with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                            client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                            client.disconnect()
                    else:log('Kraken duplicate')
                elif(len(words)>1 and result2.lower().find('and more')>-1):
                    final = "Kraken lists few tokens ([link]("+str(hrefer)+')):\n\n'
                    for h in range(len(words)):
                        tag = ticker_improve(words[h])
                        if(duplicate_check('kraken',tag) == False):final = final + tag + " ([pair](https://pro.kraken.com/app/trade/" + str(words[h].lower()) + "-usd))\n"
                    final = final + "and more...\n\n@rickler_alerts"
                    if(duplicate_check('kraken',words[1].upper()) == False):
                        with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                            client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                            client.disconnect()
                    else:log('Kraken duplicate')
                elif(len(words)>1):
                    final = "Kraken lists "+str(len(words))+" tokens ([link]("+str(hrefer)+')):\n\n'
                    for h in range(len(words)):
                        tag = ticker_improve(words[h])
                        if(duplicate_check('kraken',tag) == False):final = final + tag + " ([pair](https://pro.kraken.com/app/trade/" + str(words[h].lower()) + "-usd))\n"
                    final = final + "\n@rickler_alerts"
                    if(duplicate_check('kraken',words[1].upper()) == False):
                        with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                            client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                            client.disconnect()
                    else:log('Kraken duplicate')
        else:log('Kraken filtered')

def check_bithumb():
    global prx,bithumb1,bithumb2,build,bitscore
    if (bitscore%100!=0): return log(str(bitscore))
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
              'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
              'Accept-Encoding':'gzip, deflate, br',
                'Accept-Language':'en-US,en;q=0.9',
                'Cache-Control':'no-cache',
                'Dnt':'1',
                'Pragma':'no-cache',
                'Sec-Ch-Ua':'''"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"''',
                'Sec-Ch-Ua-Mobile':'?0',
                'Sec-Ch-Ua-Platform':'''"Windows"''',
              } 
    response1 = json.loads(requests.get(f'https://feed.bithumb.com/_next/data/{build}/notice.json?category=8&keyword=&page=1', headers = header, proxies=dict(https=static_prx), timeout=5).text) 
    current_id1 = response1["pageProps"]["noticeList"][0]["id"]
    log(str(current_id1))
    response2 = json.loads(requests.get(f'https://feed.bithumb.com/_next/data/{build}/notice.json?category=9&keyword=&page=1', headers = header, proxies=dict(https=static_prx), timeout=5).text) 
    current_id2 = response2["pageProps"]["noticeList"][0]["id"]
    log(str(current_id2))
    #last_id = 77777
    #current_id2 = 16444488
    #print(current_id)
    if (bithumb1 < current_id1 or bithumb2 < current_id2):
        log('Bithumb finded')
        if (bithumb1 < current_id1):
            bithumb1 = current_id1
            last_id = current_id1
            data = response1["pageProps"]["noticeList"][0]["title"]
        if (bithumb2 < current_id2):
            bithumb2 = current_id2
            last_id = current_id2
            data = response2["pageProps"]["noticeList"][0]["title"]
        log(data)
        #примеры заголовков
        #data = '[이벤트] 주피터(JUP1) 원화 마켓 추가 기념 에어드랍 이벤트'
        #data = '[마켓 추가] 주피터(JUP) 원화 마켓 추가(거래 오픈 오후 2시)'
        #data = '[이벤트] 엑셀라(WAXL) 원화 마켓 추가 기념 에어드랍 이벤트'
        #data = '[마켓 추가] 엑셀라(WAXL), 일드길드게임즈(YGG) 원화 마켓 추가'
        #data = '[이벤트] 만타 네트워크(MANTA) 마켓 추가 기념 사전 이벤트'
        #data = '[이벤트] 네오(NEO), 가스(GAS) 원화 마켓 추가 기념 에어드랍 이벤트'
        #data = '[이벤트] 위믹스(WEMIX) 원화 마켓 추가 기념 "다시 WEMIX" 이벤트 (쿠폰등록 오픈)'
        #data = '[마켓 추가] 에이프코인(APE), 렌더토큰(RNDR), 팬텀(FTM) 원화 마켓 추가 (업데이트 - 거래 시작 시간 변경)'
        if (data.lower().find('원화 마켓') >= 0 or data.lower().find('마켓 추가') >= 0):
            tickers = data.split()
            words = []
            del_index = []
            final=''
            for line in tickers: words += [w for w in line.split() if w.isupper()]  # ищем слово КАПСОМ
            for d in range(len(words)):
                l = "".join(c for c in words[d] if c.isalnum())
                words[d] = re.sub(r'[^a-zA-Z0-9 ]',r'',l)
            for x in range(len(words)):  # удаляем лишние тикеры
                if (duplicate_check('bithumb',words[x]) == True):del_index = [x] + del_index
                if (words[x].find('BTC') > -1):del_index = [x] + del_index
            for z in range(len(del_index)):  # удаляем лишние тикеры
                words.pop(del_index[z])
            if (len(words) == 1):
                ticker = words[0]
                tag = ticker_improve(ticker)
                final = "🔥 Bithumb lists " + tag + " ([link](https://feed.bithumb.com/notice/" + str(
                    last_id) + ") / [pair](https://www.bithumb.com/react/trade/order/" + str(
                    ticker.upper()) + "-KRW))\n\n@rickler_alerts"
            elif (len(words) > 1):
                final = "🔥🔥🔥 Bithumb lists "+str(len(words))+" tokens ([link](https://feed.bithumb.com/notice/"+str(last_id)+')):\n\n'
                for h in range(len(words)):
                    tag = ticker_improve(words[h])
                    final = final + tag + " ([pair](https://www.bithumb.com/react/trade/order/" + str(words[h].upper()) + "-KRW))\n"
                final = final + "\n@rickler_alerts"
            if(len(final)>0):
                with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                    client.send_message(ALERTS_CHANNEL, final, link_preview=False)
                    client.disconnect()
            else:log('Bithumb IFELSE error or duplicate')
        else:log(' Bithumb filtered!')

def mexc_collect(idm,ticker):
    # MEXC иногда публикует несколько листингов подряд, поэтому сначала складываем их в collected.txt.
    # Отдельный скрипт mexc.py позже объединяет их в одно сообщение.
    collect = []
    file = open('collected.txt', 'r', encoding="utf-8")
    while True:
        line = file.readline()
        if not line:break
        collect.append(line.strip())
        file.close
    if(len(collect)==0):
        with open('collected.txt', 'a', encoding="utf-8") as f_in:
            f_in.write(str(time.time())+'\n')
    with open('collected.txt', 'a', encoding="utf-8") as f_in:
        f_in.write(str(idm)+'\n')
    with open('collected.txt', 'a', encoding="utf-8") as f_in:
        f_in.write(str(ticker)+'\n')
    log(' MEXC added '+str(ticker))

def check_mexc():
    global prx,mexc_latest
    base_url = "https://www.mexc.com/help/announce/api/en-US/section/360000254192/articles?page=1&perPage=60"
    response = requests.get(base_url)
    data = response.json().get("data", {}).get("results", [])
    log(data[0]["title"])
    if mexc_latest is None or mexc_latest != data:
        log('MEXC finded')
        for article in data:
            title = article.get("title", "")
            news_id = article.get("id")
            # Проверяем, содержит ли заголовок ключевые фразы
            if ("[Initial Listing]" in title or "MEXC Kickstarter" in title or "MEXC Will List" in title or "Innovation Zone" in title or "Meme+ Trading Zone" in title) and "Futures" not in title:
                start = title.find('(')
                end = title.find(')')
                if start != -1 and end != -1:
                    ticker = title[start + 1:end].strip()
                else:
                    words = title.split()
                    for word in words:
                        if word.isupper() and any(char.isdigit() or char.isalpha() for char in word):
                            ticker = word.strip()
                            break
                    else:continue  # Пропускаем, если тикер не найден
                # Проверяем тикер на соответствие условиям
                if (ticker not in ["MEXC", "MX", "USDT", "USDC", "BTC", "ETH", "BNB"] and
                        duplicate_check('mexc', ticker) == False):
                    mexc_collect(news_id, ticker)
        # Обновляем mexc_latest только после успешной обработки данных
        mexc_latest = data
    else:
        log('MEXC filtered!')

# Первичная инициализация: выбираем proxy и запоминаем текущие последние новости.
try:
    proxySet()
    start()
    with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
        client.send_message(ADMIN_CHAT, 'Web started!', silent=True)
        client.disconnect()
except Exception as e:
    log(' launch failed '+str(e))
    for _ in range(5):
        launch_errors = launch_errors + 1
        if(launch_errors<4):
            try:
                time.sleep(5)
                proxySet()
                start()
                with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                    client.send_message(ADMIN_CHAT, 'Web started!', silent=True)
                    client.disconnect()
                break
            except Exception:continue
        else:
            msg = 'ERROR: Web parser ' + str(e)
            with TelegramClient("AlertsWeb", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                client.send_message(ADMIN_CHAT, msg)
                client.disconnect()
            log(' relaunch failed')
            break
# Основной polling-цикл: по очереди проверяем источники и логируем ошибки по каждой бирже отдельно.
while(True):
    start = time.time()
    try:proxySet()
    except Exception as e:log('proxy set err '+str(e))  
    log(prx)
    try:
        log('Kraken start')
        check_kraken()
        log('Kraken end')
    except Exception as e:log('Kraken err '+str(e))
    try:
        log('nOKX start')
        check_okx()
        log('nOKX end')
    except Exception as e:log('nOKX err '+str(e))  
    try:
        log('Upbit start')
        check_upbit()
        log('Upbit end')
    except Exception as e:log('Upbit err '+str(e))
    try:
        log('Bitfinex start')
        check_bitfinex()
        log('Bitfinex end')
    except Exception as e:log('Bitfinex err '+str(e))
    try:
        log('Binance start')
        check_binance() 
        log('Binance end')
    except Exception as e:log('Binance err '+str(e))
    try:
        log('Huobi start')
        check_htx()
        log('Huobi end') 
    except Exception as e:log('Huobi err '+str(e))
    try:
        log('MEXC start')
        check_mexc()
        log('MEXC end')
    except Exception as e:log('MEXC err '+str(e)) 
    end = time.time() - start
    if(end>27):log(str(prx)+' delay '+str(end))
    log('ended --------------------')
