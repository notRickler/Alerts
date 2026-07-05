from telethon.sync import TelegramClient
from telethon import functions, utils
from telethon.tl.types import MessageEntityTextUrl
from datetime import datetime
import re
import demoji
import time
import configparser

# Данные Telegram API вынесены в переменные, чтобы их было легко заменить перед запуском.
api_id = 123456
api_hash = 'your_api_hash'

# Кому в Telegram отправлять служебные уведомления о запуске и ошибках.
# Можно указать как канал, так и пользователя, без @
ADMIN_CHAT = 'username'

# Канал Telegram, куда публикуются готовые алерты о листингах.
# Можно указать как канал, так и пользователя, без @
ALERTS_CHANNEL = 'channel_username'

# Небольшая пауза перед запуском, чтобы другие скрипты/сессии успели стартовать.
time.sleep(3)

errors = 0

def times():
    return datetime.now().strftime('%d.%m [%H:%M:%S.%f')[:-3]+str('] ')

with TelegramClient("AlertsTG", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
    client.send_message(ADMIN_CHAT, 'Alerts started!', silent=True)
    client.disconnect()

idmsg=0 
#пояснение для списка annl
#rickler (мой айди для пинга скрипта внутри тг) 7438771641 tester (канал для тестов) 1861782948 coinlisting 1124574831, New Listings Feed 2043434663, Newsmaker 1461988268,  bingx (отключен и убран из annl) 1590958755
#остальные id можно посмотреть в функции forwarder()
# Список Telegram-каналов, которые скрипт читает.
# В forwarder() сообщения из остальных диалогов игнорируются.
annl = [1466097052,
        1469185142,
        1586671139,
        1168785398,
        1225840176,
        1449478440,
        1294500289,
        1128134602,
        1260376173,
        1482042623,
        1461988268,
        1124574831,
        7438771641,
        1202540487,
        1861782948,
        2043434663]

def log(text):
    with open('logsTg.txt', 'a', encoding="utf-8") as f_in:
        f_in.write(str('\n')+times()+' '+text)
    print(times()+' '+text)

log('started!')

def ticker_improve(tick):
    if any(char.isdigit() for char in tick) or len(tick)>8:res = str('''#''')+str(tick)
    else:res = str('$')+str(tick)
    res = res.upper()
    return res

def sender(mess,voice):
    # Отдельная функция отправки, чтобы парсеры бирж не создавали TelegramClient вручную.
    log('trying to send msg: '+mess)
    with TelegramClient("AlertsTG", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
        client.send_message(ALERTS_CHANNEL,mess,link_preview=False,silent=voice) #tester_27 тестовый канал rickler_alerts основной канал
        log('sent!')

def forwarder():
    # Основной проход по Telegram: ищем непрочитанные сообщения в нужных каналах и отправляем их в парсеры.
    global idmsg,for_hyper,errors
    client = TelegramClient("AlertsTG", api_id, api_hash, system_version="Windows 10CUSTOM")
    try:
        client.start()
        new_ones = []
        # Берём только диалоги с непрочитанными сообщениями, чтобы не перечитывать всю историю каналов.
        x = [[d.id] for d in client.get_dialogs() if not getattr(d.entity, 'is_private', False) and d.unread_count != 0] #получаем все диалоги (переписки, каналы) с аккаунта
        for o in range(len(x)):
            real_id, _ = utils.resolve_id(x[o][0])
            for m in range(len(annl)): #сортируем, оставляя только нужные нам диалоги по id из списка annl
                if(int(real_id)==int(annl[m])):
                    new_ones.append(real_id)
        for z in range(len(new_ones)): #в каждом диалоге проверяем количество новых сообщений
            result = client(functions.messages.GetPeerDialogsRequest(peers=[new_ones[z]]))
            start = result.dialogs[0].top_message-result.dialogs[0].unread_count+1
            end = result.dialogs[0].top_message+1
            ider = []
            for g in range(start,end): #запускаем парсинг для каждого нового сообщения
                ider.append(g)
            if(int(new_ones[z]) == 7438771641): #если пишу боту слово alerts, то в ответ он должен прислать Alerts online!, значит скрипт работает и не завис
                msg = client.get_messages(new_ones[z], ids=ider)
                if(msg[-1].text=='alerts'):
                    client.send_message(new_ones[z],'Alerts online!')
                    client.send_read_acknowledge(new_ones[z],msg[-1])
            else:
                msgs = client.get_messages(new_ones[z], ids=ider)
                client.send_read_acknowledge(new_ones[z],msgs[-1])
                for i in range(len(msgs)):
                    if(msgs[i] is not None and msgs[i].raw_text is not None):
                        text = msgs[i].raw_text
                        idmsg = str(ider[i])
                        for_hyper = msgs[i]
                        channel = str(new_ones[z])
                        log('post received '+text+' '+idmsg+' '+channel) 
                        try:
                            if (msgs[i] is not None and for_hyper.raw_text is not None and channel=="1124574831"):coinlisting(text,for_hyper) #нет смысла фильтровать как остальные пересылки, тк канал специализируется только на листингах
                            elif (msgs[i] is not None and for_hyper.raw_text is not None and channel=="2043434663"):coinbase_alt3(text,for_hyper) #New Listings Feed изначально использовался только для Coinbase, но потом добавил на всякий случай парсинг Binance, OKX и Robinhood
                            elif (msgs[i] is None or for_hyper.raw_text is None or is_listing_message(text)==0 or text.lower().find('weekly report')>=0 or text.lower().find('twitter space')>=0 or text.lower().find('bitget research daily report')>=0 or text.lower().find('list of')>=0 or text.lower().find('top list')>=0 or text.lower().find('listen up')>=0 or text.lower().find('packing list')>=0 or text.lower().find('winner list')>=0 or text.lower().find('demo day')>=0):log(str(channel)+' filtered')
                            else:
                                log(str(channel)+' not filtered')
                                if (channel=="1466097052"):cl(text)
                                if (channel=="1586671139"):gate(text)
                                if (channel=="1168785398"):ascend(text)
                                if (channel=="1225840176"):ccom(text)
                                if (channel=="1449478440"):bybit(text)
                                if (channel=="1294500289"):huobi(text)
                                if (channel=="1128134602"):kucoin(text)
                                if (channel=="1260376173"):bitget(text)
                                if (channel=="1461988268"):coinbase(text,for_hyper) #Newsmaker
                                if (channel=="1202540487"):bithumb(text) #bithumb telegram
                                #if (channel=="1590958755"):bingx(text,for_hyper) отключил из-за сложности парсинга
                                #if (channel=="1861782948"):bingx(text,for_hyper) #тестовый канал tester, включаю когда пишу обновы, пересылаю в него посты и там же получаю результат парсинга
                        except Exception as e:
                            if(errors<10):
                                log('main error #' + str(errors) + ' ' + str(e))
                                errors += 1
                            else:print(errors)
        log('loop alive')
    finally:
        client.disconnect()

def is_listing_message(msg): #общий фильтр для всех бирж, если есть одна из этих фраз, то скорее всего там новый листинг и запускается функция для конкретной биржи
    # Это грубый предварительный фильтр: он отсеивает явно нерелевантные посты до запуска парсеров конкретных бирж.
    if (msg.lower().find(' list')>=0 or
        msg.lower().find(' lists')>=0 or
        msg.lower().find(' listed')>=0 or
        msg.lower().find(' listing')>=0 or
        msg.lower().find('get ready')>=0 or
        msg.lower().find('launchpool')>=0 or #introducing Binance
        msg.lower().find('launchpad')>=0 or #bybit
        msg.lower().find('mining')>=0 or # without OKB
        msg.lower().find('token sale')>=0 or # OKX + kucoin - announcement + without 'the price'
        msg.lower().find('ieo')>=0 or #FTX - about and please note
        msg.lower().find('on bybit launchpad: now live')>=0 or
        msg.lower().find('session of launchpad')>=0 or #MEXC -will launch
        msg.lower().find('fractional')>=0 or #KuCoin
        msg.lower().find('burningdrop')>=0 or
        msg.lower().find('lockdrop: stake to share')>-1 or
        msg.lower().find('will be live for spot trading') >= 0 or  #Bybit
        msg.lower().find('live for trading on bybit spot') >= 0 or
        msg.lower().find('''live on bybit's spot''') >= 0 or
        msg.lower().find('byvotes') >= 0 or
        msg.lower().find('bystarter') >= 0 or
        msg.lower().find('token splash') >= 0 or
        msg.lower().find('#dailyshare') >= 0 or
        msg.lower().find('deposits are open 🟢') >= 0 or
        msg.lower().find('now live on bybit spot') >= 0 or
        msg.lower().find('gate.io startup free offering') >= 0 or
        msg.lower().find('gate.io startup initial') >= 0 or
        msg.lower().find('gate.io startup offering') >= 0 or
        msg.lower().find('gate.io startup prime project') >= 0 or
        msg.lower().find('gt holders exclusive') >= 0 or
        msg.lower().find('gt holders-exclusive') >= 0 or
        msg.lower().find('gt holder exclusive') >= 0 or
        msg.lower().find('gt holder-exclusive') >= 0 or
        msg.lower().find('#startupmining') >= 0 or
        msg.lower().find('initial offering') >= 0 or
        msg.lower().find(' ido project')>-1 or
        msg.lower().find('bybit web3 ido')>-1 or
        msg.lower().find('new ido')>-1 or
        msg.lower().find('binance hodler')>-1 or
        msg.lower().find('hodler airdrop')>-1 or
        msg.lower().find('bitget launchpad')>-1 or
        (msg.lower().find('#launchpad')>-1 and msg.lower().find('bitget')>-1) or
        (msg.lower().find('new')>-1 and msg.lower().find('coinlist')>-1 and msg.lower().find('sale starts')>-1) or
        msg.lower().find('kickstarter')>-1 or
        msg.lower().find('#coinbaseassets')>-1 or
        msg.lower().find('sales.coinlist.co')>=0 or
        msg.lower().find('#bybit | new #tokensplash')>=0 or
        msg.lower().find('weekly platform updates')>=0 or
        msg.lower().find('원화 마켓')>=0 or
        msg.lower().find('마켓 추가')>=0 or
        msg.lower().find('kucoinspotlight')>=0 or
        msg.lower().find('''bybit's weekly''')>=0 or
        msg.lower().find('thrilled to announce the listing') > -1 ) or (msg.lower().find('coming soon') > -1 and msg.lower().find('spot') > -1) or (msg.lower().find('deposits are open') > -1 and msg.lower().find('selected regions') > -1):
        log(" finded!")
        return True
    else:return False

def duplicate_check(ex,ticker):
    # Общая защита от повторов: биржи могут несколько раз писать о том же токене.
    # Если тикер новый, функция добавляет его в duplicates.txt и обновляет счётчик в data.ini.
    match=0
    ticker=ticker.upper()
    duplicates = []
    file = open('duplicates.txt', 'r')
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
        config = configparser.ConfigParser(strict=False)
        config.read("data.ini")
        if(ex=="coinlistings"):config['Listings']['coinlist']=str(int(config['Listings']['coinlist'])+1)
        if(ex=="mexc"):config['Listings']['mexc']=str(int(config['Listings']['mexc'])+1)
        if(ex=="gate"):config['Listings']['gate']=str(int(config['Listings']['gate'])+1)
        if(ex=="ascend"):config['Listings']['ascendex']=str(int(config['Listings']['ascendex'])+1)
        if(ex=="ccom"):config['Listings']['cryptocom']=str(int(config['Listings']['cryptocom'])+1)
        if(ex=="bybit"):config['Listings']['bybit']=str(int(config['Listings']['bybit'])+1)
        if(ex=="bitget"):config['Listings']['bitget']=str(int(config['Listings']['bitget'])+1)
        if(ex=="kucoin"):config['Listings']['kucoin']=str(int(config['Listings']['kucoin'])+1)
        if(ex=="kucoinetf"):config['Listings']['kucoin']=str(int(config['Listings']['kucoin'])+1)
        if(ex=="bingx"):config['Listings']['bingx']=str(int(config['Listings']['bingx'])+1)
        if(ex=="coinbaselist"):config['Listings']['coinbase']=str(int(config['Listings']['coinbase'])+1)
        if(ex=="binlist"):config['Listings']['binance']=str(int(config['Listings']['binance'])+1)
        if(ex=="binallist"):config['Listings']['binance']=str(int(config['Listings']['binance'])+1)
        if(ex=="upbit"):config['Listings']['upbit']=str(int(config['Listings']['upbit'])+1)
        if(ex=="bithumb"):config['Listings']['bithumb']=str(int(config['Listings']['bithumb'])+1)
        if(ex=="okx"):config['Listings']['okx']=str(int(config['Listings']['okx'])+1)
        if(ex=="robinhood"):config['Listings']['robinhood']=str(int(config['Listings']['robinhood'])+1)
        with open('data.ini', 'w') as config_file:
            config.write(config_file)
        return False

def mexc_collect(idm,ticker):
    # MEXC-листинги сначала складываются в collected.txt, чтобы mexc.py мог собрать несколько новостей в одно сообщение.
    collect = []
    file = open('collected.txt', 'r')
    while True:
        line = file.readline()
        if not line:break
        collect.append(line.strip())
        file.close
    if(len(collect)==0):
        with open('collected.txt', 'a') as f_in:
            f_in.write(str(time.time())+'\n')
    with open('collected.txt', 'a') as f_in:
        f_in.write(str(idm)+'\n')
    with open('collected.txt', 'a') as f_in:
        f_in.write(str(ticker)+'\n')
    log('mexc added '+str(ticker))

# Ниже идут парсеры конкретных Telegram-каналов/бирж.
# Каждый парсер знает свой формат постов и пытается достать тикер, ссылку и тип события.
def cl(msg):
    global idmsg
    if(msg.lower().find('recap')==-1 and msg.lower().find('last week')==-1): #просто условие-затычка
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x].find('SOON')>-1):del_index = [x] + del_index
            if(words[x].find('NEW')>-1):del_index = [x] + del_index
            if(words[x].find('TRADING')>-1):del_index = [x] + del_index
            if(words[x].find('LISTING')>-1):del_index = [x] + del_index
            if(words[x].find('NOW')>-1):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        if((msg.lower().find('new')>=0 and msg.lower().find('sale starts')>=0) or (msg.lower().find('sale')>=0 and msg.lower().find('the sale begins')>=0 and msg.lower().find('price')>=0 and msg.lower().find('initial purchase limits')>=0) or (msg.lower().find('token launch')>=0 and msg.lower().find('initial purchase limits')>=0) or (msg.lower().find('price')>=0 and msg.lower().find('supply')>=0 and msg.lower().find('initial purchase limits')>=0)):
            if (msg.lower().find('have you registered')==-1 and msg.lower().find('yet?')==-1 and msg.lower().find('a-deep-dive')==-1 and msg.lower().find('deep dive')==-1 and msg.lower().find('dive in')==-1):
                final = "🔥 CoinList announced new token sale! ([link](https://t.me/coinlistofficialchannel/"+str(idmsg)+"))\n\n@rickler_alerts"
                sender(final,False)
            else:log('CL sales filtered')
        elif(msg.lower().find('listing:')>=0 or msg.lower().find('listings:')>=0 or msg.lower().find('listings:')>=0 or msg.lower().find('will be list')>=0 or msg.lower().find('will list')>=0 or msg.lower().find('will be listing')>=0):
            ticker = words[0]
            if (duplicate_check('coinlistings',ticker) == False):
                tag = ticker_improve(ticker)
                final = "CoinList lists " + tag + " ([link](https://t.me/coinlistofficialchannel/"+str(idmsg)+") / [pair](https://pro.coinlist.co/trader/"+str(ticker.upper())+"-USDT))\n\n@rickler_alerts"
                sender(final,False)
            else:log('CL duplicate ticker')
        else:log('cl filtered')
    else:log('cl 3 filtered')

def mexc(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    imsg = msg
    if(msg.lower().find('session of launchpad')>-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        if(msg.lower().find('session of launchpad')>=0 and msg.lower().find('ongoing events')==-1 and msg.lower().find('daily news')==-1 and msg.lower().find('draw results for the')==-1):
            ticker = words[0]
            tag = ticker_improve(ticker)
            final = "MEXC announced " + tag + " token sale! ([link](https://t.me/MEXCofficialNews/"+str(idmsg)+"))\n\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('daily news')==-1 and
        msg.lower().find('winner')==-1 and
        msg.lower().find('weekly event')==-1 and
        msg.lower().find('ongoing events')==-1 and
        msg.lower().find('m-day')==-1 and
        msg.lower().find('futures')==-1 and
        msg.lower().find('margin')==-1 and
        msg.lower().find('trading pairs')==-1):
        if(msg.lower().find('will be listed')>=0 or msg.lower().find('will list')>=0 or msg.lower().find('kickstarter')>=0 or msg.lower().find('listing arrangement')>=0 or msg.lower().find('will launch')>=0 or msg.lower().find('new listing alert')>=0 or msg.lower().find('usdt trading:')>=0 or msg.lower().find('trading in the innovation')>=0 or msg.lower().find('estimated trading:')>=0):
            msg = str(msg.split('\n\n', 1)[1])
            tickers=msg.split()
            words=[]
            track=''
            for line in tickers:words += [w for w in line.split() if w.startswith('$')]
            for line in tickers:words += [w for w in line.split() if w.endswith('/USDT')]
            for line in tickers:words += [w for w in line.split() if w.startswith('#')]
            for d in range(len(words)):
                words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
            if(len(words)>0):track=words[0]
            else:track=''
            if(track=='MEXCK' or track=='MEXC' or track=='MX' or track=='UTC' or track.isdigit() or track=='' or len(track)>15):
                track=''
                for g in range(0,len(msg)-1):
                    if((msg[g].isupper() and msg[g+1].isdigit() and msg[g].isalpha()) or (msg[g].isdigit() and msg[g+1].isupper() and msg[g+1].isalpha()) or (msg[g].isupper() and msg[g+1].isupper() and msg[g+1].isalpha())): #
                        for h in range(10):
                            if((msg[g+h].isupper() and msg[g+h].isalpha()) or msg[g+h].isdigit()):track=track+msg[g+h]
                            if(msg[g+h]=='(' or msg[g+h]==')' or msg[g+h]==' ' or msg[g+h]=='/' or (msg[g+h].isalpha()==False and msg[g+h].isdigit()==False)):
                                if(len(track)<2 or track=='MEXCK' or track=='MEXC' or track=='MX' or track=='NFT'):
                                    track=''
                                    break
                                else:break
                    if(len(track)>2):break
            words.append(track)
            del_index = []
            for x in range(len(words)): #все # и $ с OKX
                if(words[x].lower()=="mx"):del_index = [x] + del_index
                if(words[x].lower()=="mexck"):del_index = [x] + del_index
                if(words[x].lower()=="mexc"):del_index = [x] + del_index
                if(words[x].lower()=="mexckickstarter"):del_index = [x] + del_index
                if(words[x].lower()=="nft"):del_index = [x] + del_index
                if(words[x].lower()=="ai"):del_index = [x] + del_index
            for z in range(len(del_index)): #удаляем все с OKX
                words.pop(del_index[z])
            if(words[0].upper().endswith('USDT')==True and len(words[0])>=5):
                words[0]=words[0][:-4]
                for d in range(len(words)):
                    words[d]="".join(c for c in words[d] if c.isalnum())
            if(imsg.lower().find('listing')>-1 or imsg.lower().find('list')>-1 or (imsg.lower().find('will launch')>-1 and imsg.lower().find('trading')>-1) or (imsg.lower().find('kickstarter')>-1 and imsg.lower().find('trading')>-1) or (imsg.lower().find('kickstarter')>-1 and imsg.lower().find('(utc)')>-1)):
                ticker = words[0]
                if (duplicate_check('mexc',ticker) == False and ticker.isupper() == True and ticker != 'MX'):
                    mexc_collect(idmsg,ticker)
                else:log('Mexc duplicate or notUpper ticker '+ticker)
        else:log('mexc filtered 1')
    else:log('mexc filtered 2')

def gate(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    imsg = msg
    if(msg.lower().find('overview')==-1 and
        msg.lower().find('quiz')==-1 and
        msg.lower().find('giveaway')==-1 and
        msg.lower().find('report')==-1 and
        msg.lower().find('perpetual')==-1 and
        msg.lower().find('futures')==-1 and
        msg.lower().find('news channel')==-1 and
        msg.lower().find('lucky wheel')==-1 and
        msg.lower().find('listed on')==-1 and
        msg.lower().find('survey')==-1 and
        msg.lower().find('listed in')==-1 and
        msg.lower().find('startup mining celebration')==-1 and
        msg.lower().find('daily crypto trending news')==-1 and
        msg.lower().find('vote to')==-1 and
        msg.lower().find('listings performance')==-1 and
        msg.lower().find('vote for')==-1):
        if(msg.lower().find('#startupmining')<1 and msg.lower().find('initial offering')<1 and msg.lower().find('startup free offering')<1 and msg.lower().find('startup initial free')<1 and msg.lower().find('startup prime project')<1 and msg.lower().find('hodler airdrop')<1):msg = str(msg.split('\n\n', 1)[1])
        words=['']
        track=''
        for g in range(len(msg)):
            if(msg[g]=='('):
                for h in range(len(msg)-g):
                    if(msg[g+h].isupper() or msg[g+h].isdigit()):track=track+msg[g+h]
                    if(msg[g+h]==')' or msg[g+h]==' ' or msg[g+h]=='/'):break
                break
        if(track=='UTC' or track=='AM' or track=='PM' or track=='GT'):
            track=''
            for g in range(len(msg)):
                if(((msg[g].isupper() and msg[g+1].isdigit()) or (msg[g].isdigit() and msg[g+1].isupper()) or (msg[g].isupper() and msg[g+1].isupper()))
                   and msg[g]+msg[g+1]!='AM' and msg[g]+msg[g+1]!='PM' and msg[g]+msg[g+1]!='GT'):
                    for h in range(len(msg)-g):
                        if(msg[g+h].isupper() or msg[g+h].isdigit()):track=track+msg[g+h]
                        if(msg[g+h]==')' or msg[g+h]==' ' or msg[g+h]=='/'):break
                    break
        if(track=='' or track=='UTC' or track=='AM' or track=='PM' or track=='GT' or track=='USDT' or track=='USDC' or track=='BTC' or track=='ETH'):
            tickers=msg.split()
            words=[]
            for line in tickers:words += [w for w in line.split() if w.startswith('$')]
            for line in tickers:words += [w for w in line.split() if w.startswith('#')]
            for d in range(len(words)):
                words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
            del_index = []
            for x in range(len(words)): #все лишние слова
                if(words[x].find('UTC')>-1):del_index = [x] + del_index
                if(words[x].find('USDC')>-1):del_index = [x] + del_index
                if(words[x].find('USDT')>-1):del_index = [x] + del_index
                if(words[x].find('BTC')>-1):del_index = [x] + del_index
                if(words[x].find('ETH')>-1):del_index = [x] + del_index
            for z in range(len(del_index)): #удаляем все лишние слова
                words.pop(del_index[z])
            track=words[0]
        words[0]=track
        #for line in tickers:words += [w for w in line.split() if w.startswith('$')] #находим все # и $
        #for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        #for line in tickers:words += [w for w in line.split() if w.isupper()] #ищем слово КАПСОМ
        #for d in range(len(words)):
            #words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        #del_index = []
        #for z in range(len(del_index)): #удаляем все с OKX
            #words.pop(del_index[z])
        if(imsg.lower().find('listing')>-1 or imsg.lower().find('list')>-1 or imsg.lower().find('free offering')>-1 or imsg.lower().find('startup initial')>-1 or imsg.lower().find('startup prime project')>-1 or imsg.lower().find('initial')>-1 or (imsg.lower().find('hodler airdrop')>-1 and imsg.lower().find('subscription')>-1)):
            ticker = words[0].upper()
            if (duplicate_check('gate',ticker) == False and len(ticker)>=1):
                tag = ticker_improve(ticker)
                final = "Gate lists " + tag + " ([link](https://t.me/GateOfficialNews/"+str(idmsg)+") / [pair](https://www.gate.io/trade/"+str(ticker)+"_USDT))\n\n@rickler_alerts"
                sender(final,True)
            else:log('Gate duplicate ticker')
        else:log('Gate filtered 2')
    else:log('gate filtered')

def ascend(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    if(msg.lower().find('listing')>=0 and msg.lower().find('leveraged')==-1 and msg.lower().find('delist')==-1 and msg.lower().find('perpetual futures')==-1):
        words=['']
        track=''
        for g in range(len(msg)):
            if(msg[g]=='('):
                for h in range(len(msg)-g):
                    if(msg[g+h].isupper() or msg[g+h].isdigit()):track=track+msg[g+h]
                    if(msg[g+h]==')' or msg[g+h]==' ' or msg[g+h]=='/'):break
                break
        if(track=='UTC' or track=='EX' or track=='NFT' or track=='P2E' or track=='IEO' or track=='IDO' or track==''):
            track=''
            for g in range(27,len(msg)):
                if((msg[g].isupper() and msg[g+1].isdigit() and msg[g].isalpha()) or (msg[g].isdigit() and msg[g+1].isupper() and msg[g+1].isalpha()) or (msg[g].isupper() and msg[g+1].isupper() and msg[g+1].isalpha())): #
                    for h in range(len(msg)-g):
                        if(msg[g+h].isupper() or msg[g+h].isdigit()):track=track+msg[g+h]
                        if(msg[g+h]==')' or msg[g+h]==' ' or msg[g+h]=='/' or (msg[g+h].isalpha()==False and msg[g+h].isdigit()==False)):
                            if(len(track)<2 or track=='UTC' or track=='NFT'):track=''
                            else:break
                    break
        words[0]=track
        ticker = words[0].upper()
        if (duplicate_check('ascend',ticker) == False):
            tag = ticker_improve(ticker)
            final = "AscendEX lists " + tag + " ([link](https://t.me/AscendEXAnnoucement/"+str(idmsg)+") / [pair](https://ascendex.com/en/cashtrade-spottrading/usdt/"+str(ticker.lower())+"))\n\n@rickler_alerts"
            sender(final,True)
        else:log('ascend duplicate')
    else:log('ascend filtered')

def ccom(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    '''msg.lower().find('vote')==-1 and
        msg.lower().find('margin')==-1 and
        msg.lower().find('perpetual')==-1 and
        msg.lower().find('futures')==-1 and
        msg.lower().find('this week')==-1 and
        msg.lower().find('are now available')==-1 and
        msg.lower().find('the weekly nft')==-1 and
        msg.lower().find('target price orders')==-1 and
        msg.lower().find('list')>-1 and
        msg.lower().find('join now')==-1 and
        msg.lower().find('listed on')==-1 and'''
    if((msg.lower().find('is now listed in the crypto.com')>-1 and msg.lower().find('exchange')>-1) or (msg.lower().find('will list')>-1 and msg.lower().find('exchange')>-1) or (msg.lower().find('is now listed')>-1 and msg.lower().find('exchange')>-1)):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for line in tickers:words += [w for w in line.split() if w.startswith('#')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x].find('UTC')>-1):del_index = [x] + del_index
            if(words[x].find('USDC')>-1):del_index = [x] + del_index
            if(words[x].find('USDT')>-1):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        #if(msg.lower().find('lists')>-1 or msg.lower().find('listed')>-1)
        if (len(words[0])>1):
            ticker = words[0].upper()
            if (duplicate_check('ccom',ticker) == False):
                tag = ticker_improve(ticker)
                final = "CryptoCom lists " + tag + " ([link](https://t.me/CryptoComOfficialAnnouncements/"+str(idmsg)+") / [pair](https://crypto.com/exchange/trade/"+str(ticker)+"_USD))\n\n@rickler_alerts"
                sender(final,True)
            else:log('ccom duplicate')
    else:log('ccom filtered')

def bybit(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    if(msg.lower().find('now live on bybit launchpad')>-1 or
        msg.lower().find('bybit launchpad: now live')>-1 or
        msg.lower().find('coming soon to bybit launchpad')>-1 or #New Launchpad Project
        msg.lower().find('new launchpad')>-1 or
        msg.lower().find('launchpad: subscription')>-1 or
        (msg.lower().find('bystarter')>-1 and msg.lower().find('will')>-1) and msg.lower().find('[live now]')==-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x]=='UTC'):del_index = [x] + del_index
            if(words[x]=='USDC'):del_index = [x] + del_index
            if(words[x]=='USDT'):del_index = [x] + del_index
            if(words[x]=='IEO'):del_index = [x] + del_index
            if(words[x]=='KYC'):del_index = [x] + del_index
            if(words[x]=='BIT'):del_index = [x] + del_index
            if(words[x]=='MNT'):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        ticker = words[0]
        if (duplicate_check('bybit',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 Bybit announced " + tag + " launchpad! ([link](https://t.me/Bybit_Announcements/"+str(idmsg)+") / [pair](https://www.bybit.com/en-US/trade/spot/"+str(ticker)+"/USDT))\n\n@rickler_alerts"
            sender(final,False)
        else:log('bybit ieo duplicate')
    elif(msg.lower().find('new launchpool')>-1 or
        msg.lower().find('bybit launchpool: stake')>-1 or
        msg.lower().find('launchpool is excited')>-1 or
        msg.lower().find('launchpool: stake')>-1 or
        (msg.lower().find('coming soon')>-1 and msg.lower().find('launchpool')>-1) and msg.lower().find('[live now]')==-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x]=='UTC'):del_index = [x] + del_index
            if(words[x]=='USDC'):del_index = [x] + del_index
            if(words[x]=='USDT'):del_index = [x] + del_index
            if(words[x]=='IEO'):del_index = [x] + del_index
            if(words[x]=='KYC'):del_index = [x] + del_index
            if(words[x]=='BIT'):del_index = [x] + del_index
            if(words[x]=='MNT'):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        ticker = words[0]
        if (duplicate_check('bybit',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 Bybit announced " + tag + " launchpool! ([link](https://t.me/Bybit_Announcements/"+str(idmsg)+") / [pair](https://www.bybit.com/en-US/trade/spot/"+str(ticker)+"/USDT))\n\n@rickler_alerts"
            sender(final,False)
        else:log('bybit ieo duplicate')
    elif((msg.lower().find(' ido project')>-1 or
        msg.lower().find('bybit web3 ido')>-1 or
        msg.lower().find('new ido')>-1) and msg.lower().find('[live now]')==-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.startswith("'")]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x]=='UTC'):del_index = [x] + del_index
            if(words[x]=='USDC'):del_index = [x] + del_index
            if(words[x]=='USDT'):del_index = [x] + del_index
            if(words[x]=='IDO'):del_index = [x] + del_index
            if(words[x]=='BIT'):del_index = [x] + del_index
            if(words[x]=='MNT'):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        ticker = words[0]
        if (duplicate_check('bybit',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 Bybit Web3 announced " + tag + " IDO! ([link](https://t.me/Bybit_Announcements/"+str(idmsg)+") / [pair](https://www.bybit.com/en-US/trade/spot/"+str(ticker)+"/USDT))\n\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('live for trading')==-1 and
        msg.lower().find('launchpad')==-1 and
        msg.lower().find('[live now]')==-1 and
        msg.lower().find('vote')==-1 and
        msg.lower().find('competition')==-1 and
        msg.lower().find('margin')==-1 and
        msg.lower().find('perpetual')==-1 and
        msg.lower().find('futures')==-1 and
        msg.lower().find('token swap')==-1 and
        msg.lower().find('glassnode report')==-1 and
        msg.lower().find('weekly platform updates')==-1 and
        #msg.lower().find('airdrop')==-1 and
        msg.lower().find('get ready')==-1 and
        msg.lower().find('until')==-1 and
        msg.lower().find('on convert')==-1 and
        msg.lower().find('apy')==-1 and
        msg.lower().find('stake at least')==-1 and
        msg.lower().find('this week in bybit')==-1 and
        msg.lower().find('prediction draw')==-1 and
        msg.lower().find('winners of this week')==-1 and
        msg.lower().find('predict and win')==-1 and
        msg.lower().find('liquidity mining')==-1 or (msg.lower().find('byvotes')>-1 and msg.lower().find('live for trading')>-1) or (msg.lower().find('byvotes')>-1 and msg.lower().find('token wins')>-1) or (msg.lower().find('byvotes')>-1 and msg.lower().find('results are in')>-1) or (msg.lower().find('byvotes')>-1 and msg.lower().find('results are in')>-1) or (msg.lower().find('byvotes')>-1 and msg.lower().find('innovation zone')>-1)):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')] #находим все # и $
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.startswith('#')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x].find('UTC')>-1):del_index = [x] + del_index
            if(words[x].find('USDC')>-1):del_index = [x] + del_index
            if(words[x].find('USDT')>-1):del_index = [x] + del_index
            if(words[x]=='BIT'):del_index = [x] + del_index
            if(words[x]=='MNT'):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        ticker = words[0].upper()
        if (duplicate_check('bybit',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 Bybit lists " + tag + " ([link](https://t.me/Bybit_Announcements/"+str(idmsg)+") / [pair](https://www.bybit.com/en-US/trade/spot/"+str(ticker)+"/USDT))\n\n@rickler_alerts"
            sender(final,False)
        else:log('bybit duplicate ticker')
    else:log('bybit filtered')

def huobi(msg):
    global idmsg
    if(msg.lower().find('recap')==-1 and
        msg.lower().find('perks')==-1 and
        msg.lower().find('prize pool')==-1 and
        msg.lower().find('contract')==-1 and
        msg.lower().find('#huobiearn')==-1 and
        msg.lower().find('#htxearn')==-1 and
        msg.lower().find(' x ')==-1 and
        msg.lower().find(' vs ')==-1 and
        msg.lower().find('watchlist')==-1 and
        msg.lower().find('primevote')==-1 and
        msg.lower().find('react')==-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for line in tickers:words += [w for w in line.split() if w.isupper()] #ищем слово КАПСОМ
        for line in tickers:words += [w for w in line.split() if w.startswith('w')] #ищем слово КАПСОМ
        for d in range(len(words)):
            words[d] = "".join(c for c in words[d] if c.isalnum())  # удаляем все символы
        if (msg.lower().find('primelist') >= 0 and msg.lower().find('for sale') >= 0):
            ticker = words[0]
            if (duplicate_check('huobisale',ticker) == False):
                tag = ticker_improve(ticker)
                final = "HTX announced " + tag + " token sale! ([link](https://t.me/HuobiGlobalAnnouncementChannel/" + str(idmsg) + "))\n\n@rickler_alerts"
                sender( final, False)
            else:log('huobi duplicate sale')
        '''elif ((msg.lower().find('listing') >= 0 or msg.lower().find('list ') >= 0) and msg.lower().find('primelist') == -1 and msg.lower().find('delist') == -1):
            ticker = words[0].upper()
            if (duplicate_check('huobi',ticker) == False):
                final = "Huobi lists $" + ticker + " ([link](https://t.me/HuobiGlobalAnnouncementChannel/" + str(idmsg) + ") / [pair](https://www.huobi.com/en-us/exchange/"+str(ticker.lower())+"_usdt))\n\n@rickler_alerts"
                sender( final, False)
            else:log('huobi duplicate')
        else:log('huobi filtered')'''
    else:log('huobi filtered')

def okx(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    if(msg.lower().find('token sale')>-1 or
        msg.lower().find('mining')>-1):
        print('1')
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        if(msg.lower().find('okx')>=0 and msg.lower().find('begun')>=0 and msg.lower().find('news report')==-1):
            print('2')
            ticker = words[0]
            if (duplicate_check('okx',ticker) == False):
                tag = ticker_improve(ticker)
                final = "🔥 OKX announced " + tag + " mining! ([link](https://t.me/OKXAnnouncements/"+str(idmsg)+"))\n\n@rickler_alerts"
                sender(final,False)
        elif(msg.lower().find('token sale')>=0 and msg.lower().find('news report')==-1):
            print('3')
            ticker = words[0]
            if (duplicate_check('okx',ticker) == False):
                tag = ticker_improve(ticker)
                final = "🔥 OKX announced " + tag + " token sale! ([link](https://t.me/OKXAnnouncements/"+str(idmsg)+"))\n\n@rickler_alerts"
                sender(final,False)
    else:log('Okx filtered')

def kucoin(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    if(msg.lower().find('introducing ')>-1 and msg.lower().find('left')==-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('hi')]
        for line in tickers:words += [w for w in line.split() if w.startswith('HI')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        ticker = words[0]
        if (duplicate_check('kucoin',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 KuCoin announced " + tag + " fractional NFT sale! ([link](https://t.me/Kucoin_News/"+str(idmsg)+"))\n\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('lockdrop: stake to share')>-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        ticker = words[0]
        if (duplicate_check('kucoin',ticker) == False):
            tag = ticker_improve(ticker)
            final = "KuCoin announced " + tag + " LockDrop! ([link](https://t.me/Kucoin_News/"+str(idmsg)+") / [pair](https://www.kucoin.com/trade/"+str(ticker.upper())+"-USDT))\n\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('nft etf')>-1 and msg.lower().find('gets listed')>-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('hi')]
        for line in tickers:words += [w for w in line.split() if w.startswith('HI')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        ticker = words[0]
        if (duplicate_check('kucoin',ticker) == False):
            tag = ticker_improve(ticker)
            final = "KuCoin lists " + tag + " NFT ETF ([link](https://t.me/Kucoin_News/"+str(idmsg)+") / [pair](https://www.kucoin.com/trade/"+str(ticker.upper())+"-USDT))\n\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('token sale')>-1 and
        msg.lower().find('spotlight')>-1 and
        msg.lower().find('weekly report')==-1 and
        msg.lower().find('daily report')==-1 and
        msg.lower().find('infographic')==-1 and
        msg.lower().find('airdrop')==-1) or (msg.lower().find('spotlight')>-1 and msg.lower().find('lock in')>-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x].find('UTC')>-1):del_index = [x] + del_index
            if(words[x].find('USDT')>-1):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        ticker = words[0]
        if (duplicate_check('kucoin',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 KuCoin announced " + tag + " token sale! ([link](https://t.me/Kucoin_News/"+str(idmsg)+") / [pair](https://www.kucoin.com/trade/"+str(ticker.upper())+"-USDT))\n\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('is available')>-1 and
        msg.lower().find('burningdrop')>-1 and
        msg.lower().find('weekly report')==-1 and
        msg.lower().find('daily share')==-1 and
        msg.lower().find('infographic')==-1 and
        msg.lower().find('airdrop')==-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        ticker = words[0]
        if (duplicate_check('kucoin',ticker) == False):
            tag = ticker_improve(ticker)
            final = "KuCoin announced " + tag + " BurningDrop! ([link](https://t.me/Kucoin_News/"+str(idmsg)+") / [pair](https://www.kucoin.com/trade/"+str(ticker.upper())+"-USDT))\n\n@rickler_alerts"
            sender(final,False)
    elif((msg.lower().find('gets listed')>-1 and msg.lower().find('dailyshare')==-1) or (msg.lower().find('coming soon')>-1 and msg.lower().find('spot')>-1)):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.startswith('$')] #находим все # и $
        for line in tickers:words += [w for w in line.split() if w.startswith('#')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x].find('UTC')>-1):del_index = [x] + del_index
            if(words[x].find('NewListing')>-1):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        if (msg.lower().find('gets listed')>-1 or msg.lower().find('coming soon')>-1):
            ticker = words[0].upper()
            if (duplicate_check('kucoin',ticker) == False):
                tag = ticker_improve(ticker)
                final = "KuCoin lists " + tag + " ([link](https://t.me/Kucoin_News/"+str(idmsg)+") / [pair](https://www.kucoin.com/trade/"+str(ticker.upper())+"-USDT))\n\n@rickler_alerts"
                sender(final,False)
            else:log('kucoin duplicate ticker')
    else:log('kucoin filtered')

def bitget(msg):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    if((msg.lower().find('bitget launchpad')>-1 or msg.lower().find('#launchpad')>-1)):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x].find('UTC')>-1):del_index = [x] + del_index
            if(words[x]=='USDC'):del_index = [x] + del_index
            if(words[x]=='USDT'):del_index = [x] + del_index
            if(words[x]=='P2P'):del_index = [x] + del_index
            if(words[x]=='AM'):del_index = [x] + del_index
            if(words[x]=='PM'):del_index = [x] + del_index
            if(words[x]=='BGB'):del_index = [x] + del_index
            if(words[x]=='BWB'):del_index = [x] + del_index
            if(words[x]=='APR'):del_index = [x] + del_index
            if(words[x]=='AI'):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        ticker = words[0]
        if (duplicate_check('bitget',ticker) == False):
            tag = ticker_improve(ticker)
            final = "Bitget announced " + tag + " Launchpad! ([link](https://t.me/Bitget_Announcements/"+str(idmsg)+") / [pair](https://www.bitget.com/en/spot/"+str(ticker)+"USDT_SPBL?type=spot))\n\n@rickler_alerts"
            sender(final,False)
        else:log('bitget ieo duplicate')
    elif(msg.lower().find('poolx is listing')>-1 or msg.lower().find('to list')>-1 or msg.lower().find('to be listed')>-1 or msg.lower().find('will list')>-1 or msg.lower().find('bitget list')>-1 or msg.lower().find('will be listed')>-1):
        tickers=msg.split()
        words=[]
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        del_index = []
        for x in range(len(words)): #все # и $ с OKX
            if(words[x].find('UTC')>-1):del_index = [x] + del_index
            if(words[x].find('USDC')>-1):del_index = [x] + del_index
            if(words[x].find('USDT')>-1):del_index = [x] + del_index
            if(words[x]=='AM'):del_index = [x] + del_index
            if(words[x]=='PM'):del_index = [x] + del_index
            if(words[x]=='BGB'):del_index = [x] + del_index
            if(words[x]=='AI'):del_index = [x] + del_index
        for z in range(len(del_index)): #удаляем все с OKX
            words.pop(del_index[z])
        if(len(words)>0):
            ticker = words[0].upper()
            if (duplicate_check('bitget',ticker) == False):
                tag = ticker_improve(ticker)
                final = "Bitget lists " + tag + " ([link](https://t.me/Bitget_Announcements/"+str(idmsg)+") / [pair](https://www.bitget.com/en/spot/"+str(ticker)+"USDT_SPBL?type=spot))\n\n@rickler_alerts"
                sender(final,True)
            else:log('bitget duplicate ticker')
        else:
            for line in tickers:words += [w for w in line.split() if w.isupper()]
            for d in range(len(words)):
                words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
            del_index = []
            for x in range(len(words)): #все # и $ с OKX
                if(words[x].find('UTC')>-1):del_index = [x] + del_index
                if(words[x].find('USDC')>-1):del_index = [x] + del_index
                if(words[x].find('USDT')>-1):del_index = [x] + del_index
                if(words[x]=='AM'):del_index = [x] + del_index
                if(words[x]=='PM'):del_index = [x] + del_index
                if(words[x]=='BGB'):del_index = [x] + del_index
                if(words[x]=='BWB'):del_index = [x] + del_index
                if(words[x]=='AI'):del_index = [x] + del_index
            for z in range(len(del_index)): #удаляем все с OKX
                words.pop(del_index[z])
            if(len(words)>0):
                ticker = words[0].upper()
                if (duplicate_check('bitget',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "Bitget lists " + tag + " ([link](https://t.me/Bitget_Announcements/"+str(idmsg)+") / [pair](https://www.bitget.com/en/spot/"+str(ticker)+"USDT_SPBL?type=spot))\n\n@rickler_alerts"
                    sender(final,True)
                else:log('bitget duplicate ticker')
            else:
                ticker = 'TickerParsingError1'
                if (duplicate_check('bitget',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "Bitget lists " + tag + " ([link](https://t.me/Bitget_Announcements/"+str(idmsg)+") / [pair](https://www.bitget.com/en/spot/"+str(ticker)+"USDT_SPBL?type=spot))\n\n@rickler_alerts"
                    sender(final,True)
                else:log('bitget duplicate ticker')
    else:log('bitget filtered')

def bingx(msg,hypers):
    # Для некоторых каналов ссылка на новость берётся не из текста, а из Telegram entity MessageEntityTextUrl.
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    for url_entity, _ in hypers.get_entities_text(MessageEntityTextUrl):
        hyper = url_entity.url
    if(msg.lower().find('listed')>-1 and msg.lower().find('spot')>-1 and msg.lower().find('deposit')>-1):
        tickers=msg.split()
        track=''
        for g in range(len(msg)):
            if(msg[g]=='('):
                for h in range(len(msg)-g):
                    if(msg[g+h].isupper() or msg[g+h].isdigit()):track=track+msg[g+h]
                    if(msg[g+h]==')' or msg[g+h]==' ' or msg[g+h]=='/'):break
                break
        if(track=='UTC' or track.isdigit() or track=='' or len(track)>15):
                track=''
                for line in tickers:
                    if (line.startswith('$')):track=line
                for _ in range(len(track)):
                    track="".join(c for c in track if c.isalnum()) #удаляем все символы
        if(track.find('(UTC')>-1 or track=='UTC' or track.isdigit()==True):
            track=''
            for g in range(len(msg)):
                if((msg[g].isupper() and msg[g+1].isdigit()) or (msg[g].isdigit() and msg[g+1].isupper()) or (msg[g].isupper() and msg[g+1].isupper())):
                    for h in range(len(msg)-g):
                        if(msg[g+h].isupper() or msg[g+h].isdigit()):track=track+msg[g+h]
                        if(msg[g+h]==')' or msg[g+h]==' ' or msg[g+h]=='/'):break
                    break
        if(track.find('USDT')>-1):track=track[:-4]
        if (len(track)>1):
            ticker = track.upper()
            if (duplicate_check('bingx',ticker) == False):
                tag = ticker_improve(ticker)
                final = "BingX lists " + tag + " ([link]("+str(hyper)+") / [pair](https://bingx.com/en-us/spot/"+str(ticker)+"USDT/))\n\n@rickler_alerts"
                sender(final,True)
            else:log('bingx duplicate')
    else:log('bingx filtered')

def coinbase(msg,hypers): #Newsmaker только для Coinbase
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    if(msg.lower().find('#coinbaseassets')>-1):
        tickers=msg.split()
        words=[]
        hyper='https://twitter.com/CoinbaseAssets/'
        for line in tickers:words += [w for w in line.split() if w.startswith('(')]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        if(msg.lower().find('coinbase will add support for')>=0):
            ticker = words[0]
            if (duplicate_check('coinbaselist',ticker) == False):
                tag = ticker_improve(ticker)
                final = "🔥 Coinbase lists " + tag + " ([link]("+hyper+") / [pair](https://exchange.coinbase.com/trade/"+str(ticker)+"-USD))\n\n@rickler_alerts"
                sender(final,False)
        elif(msg.lower().find('roadmap')>=0):
            ticker = words[0]
            if (duplicate_check('coinbaseroad',ticker) == False):
                tag = ticker_improve(ticker)
                final = "Coinbase added " + tag + " to the roadmap! ([link]("+hyper+"))\n\n@rickler_alerts"
                sender(final,False)
        else:log('Coinbase inside filtered')
    else:log('Coinbase filtered')

def coinbase_alt3(msg,hypers):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    for url_entity, _ in hypers.get_entities_text(MessageEntityTextUrl):
        hyperlink = url_entity.url
    if(msg.lower().find('coinbase spot')>-1):
        tickers=msg.split()
        words=[]
        hyper=str(hyperlink)+'?source=alt-v3'
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        if(len(words)==1):
            ticker = words[0]
            if (duplicate_check('coinbaselist',ticker) == False):
                tag = ticker_improve(ticker)
                final = "🔥 Coinbase lists " + tag + " ([link]("+hyper+") / [pair](https://exchange.coinbase.com/trade/"+str(ticker)+"-USD))\n\n@rickler_alerts"
                sender(final,False)
            else:log('Coinbase Alt 3 inside 1 filtered')
        else:
            final = "🔥 Coinbase lists " + str(len(words)) + " tokens ([link]("+hyper+")):\n\n"
            for h in range(len(words)):
                tag = ticker_improve(words[h])
                if(duplicate_check('coinbaselist',tag) == False):final = final + tag + " ([pair](https://exchange.coinbase.com/trade/"+str(words[h])+"-USD))\n"
            final = final + "\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('coinbase roadmap')>-1):
        tickers=msg.split()
        words=[]
        hyper=str(hyperlink)+'?source=alt-v3'
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        if(len(words)==1):
            ticker = words[0]
            if (duplicate_check('coinbaseroad',ticker) == False):
                tag = ticker_improve(ticker)
                final = "🔥 Coinbase added " + tag + " to the roadmap ([link]("+hyper+"))\n\n@rickler_alerts"
                sender(final,False)
            else:log('Coinbase Alt 3 inside filtered')
        else:
            final = "🔥 Coinbase added " + str(len(words)) + " tokens to the roadmap ([link]("+hyper+")):\n\n"
            for h in range(len(words)):
                tag = ticker_improve(words[h])
                if(duplicate_check('coinbaseroad',tag) == False):final = final + tag + "\n"
            final = final + "\n@rickler_alerts"
            sender(final,False)
    elif(msg.lower().find('okx spot')>-1):
        tickers=msg.split()
        words=[]
        hyper=str(hyperlink)
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        ticker = words[0]
        if (duplicate_check('okx',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 OKX lists " + tag + " ([link](" + str(hyper) + "?channelId=RICKLER) / [pair](https://www.okx.com/trade-spot/"+str(ticker.lower())+"-usdt?channelId=RICKLER))\n\n@rickler_alerts"
            sender(final,False)
        else:log('OKX Alt 3 inside filtered')
    elif(msg.lower().find('binance')>-1):
        if(msg.lower().find('binance')>=0):
            data = msg
            log('binance finded')
            if(data.lower().find('binance alpha') >= 0):
                tickers = msg.split()
                words = []
                del_index = []
                for line in tickers: words += [w for w in line.split() if w.startswith('$')]
                for x in range(len(words)):  # удаляем лишние тикеры
                    if (words[x].find('old') > -1):del_index = [x] + del_index
                for z in range(len(del_index)):  # удаляем лишние тикеры
                    words.pop(del_index[z])
                for d in range(len(words)):
                        words[d] = "".join(c for c in words[d] if c.isalnum())
                if(len(words) > 0):
                    ticker = words[0]
                    tag = ticker_improve(ticker)
                    if(duplicate_check('binallist',ticker) == False):
                        final = "🔥 Binance Alpha lists " + tag + " ([link](" + str(hyperlink) + "))\n\n@rickler_alerts"
                        sender(final, False)
            elif(data.lower().find('binance spot') >= 0 or data.lower().find('binance hodler') >= 0):
                tickers = msg.split()
                words = []
                del_index = []
                for line in tickers: words += [w for w in line.split() if w.startswith('$')]
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
                        if(duplicate_check('binlist',ticker) == False):final = "🔥 Binance lists " + tag + " ([link](" + str(hyperlink) + "?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                    elif(duplicate_check('binlist','Error') == False):final = "🔥 Binance lists $TickerError ([link](" + str(hyperlink) + "?ref=JAO4CT0D))\n\n@rickler_alerts"
                if (len(words) == 1 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥 Binance lists " + tag + " ([link](" + str(hyperlink) + "?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                elif (len(words) > 1 and duplicate_check('binlist',ticker) == False):
                    final = "🔥🔥🔥 Binance lists "+str(len(words))+" tokens ([link]("+str(hyperlink)+'?ref=JAO4CT0D)):\n\n'
                    for h in range(len(words)):
                        tag = ticker_improve(words[h])
                        final = final + tag + " ([pair](https://www.binance.com/en/trade/"+str(words[h].upper())+"_USDT?ref=JAO4CT0D))\n"
                    final = final + "\n@rickler_alerts"
                sender(final, False)
            elif(data.lower().find('binance megadrop') >= 0 or data.lower().find('binance launchpad')>=0 or data.lower().find('binance launchpool')>=0):
                tickers = msg.split()
                words = []
                for line in tickers: words += [w for w in line.split() if w.startswith('$')]
                for d in range(len(words)):
                        words[d] = "".join(c for c in words[d] if c.isalnum())
                ticker = words[0]
                for d in range(len(words)):
                        words[d] = "".join(c for c in words[d] if c.isalnum())
                if(data.lower().find('megadrop') >= 0 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥🔥🔥 Binance announced " + tag + " Megadrop! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                if(data.lower().find('launchpad') >= 0 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥🔥🔥 Binance announced " + tag + " token sale! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                if(data.lower().find('launchpool') >= 0 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥🔥🔥 Binance announced " + tag + " farm! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                sender(final, False)
            else:print('Binance filtered')
    elif(msg.lower().find('robinhood spot')>-1):
        log("Robin finded")
        tickers=msg.split()
        words=[]
        hyper=str(hyperlink)
        for line in tickers:words += [w for w in line.split() if w.isupper()]
        for d in range(len(words)):
            words[d]="".join(c for c in words[d] if c.isalnum()) #удаляем все символы
        ticker = words[0]
        if (duplicate_check('robinhood',ticker) == False):
            tag = ticker_improve(ticker)
            final = "🔥 Robinhood lists " + tag + " ([link](https://robinhood.com/))\n\n@rickler_alerts"
            sender(final,False)
        else:log('Robinhood Alt 3 inside filtered')
    else:log('Alt 3 filtered')

def coinlisting(msg,hypers):
    global idmsg
    msg = demoji.replace(msg,"") #удаляем эмодзи
    if(msg.lower().find('binance')>-1 or msg.lower().find('upbit')>-1):
        tickers=msg.split()
        words=[]
        if(msg.lower().find('binance')>=0):
            data = msg
            print('binance finded')
            for url_entity, _ in hypers.get_entities_text(MessageEntityTextUrl):
                hyperlink = url_entity.url
            if((data.lower().find('will list') >= 0 and data.lower().find('options')==-1 and data.lower().find('margin')==-1 and data.lower().find('futures')==-1) or data.lower().find('hodler') >= 0):
                tickers = msg.split()
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
                        if(duplicate_check('binlist',ticker) == False):final = "🔥 Binance lists " + tag + " ([link](" + str(hyperlink) + "?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                    elif(duplicate_check('binlist','Error') == False):final = "🔥 Binance lists $TickerError ([link](" + str(hyperlink) + "?ref=JAO4CT0D))\n\n@rickler_alerts"
                if (len(words) == 1 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥 Binance lists " + tag + " ([link](" + str(hyperlink) + "?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                elif (len(words) > 1 and duplicate_check('binlist',ticker) == False):
                    final = "🔥🔥🔥 Binance lists "+str(len(words))+" tokens ([link]("+str(hyperlink)+'?ref=JAO4CT0D)):\n\n'
                    for h in range(len(words)):
                        tag = ticker_improve(words[h])
                        final = final + tag + " ([pair](https://www.binance.com/en/trade/"+str(words[h].upper())+"_USDT?ref=JAO4CT0D))\n"
                    final = final + "\n@rickler_alerts"
                sender(final, False)
            elif(data.lower().find('introducing') >= 0 and data.lower().find('on binance')>=0):
                tickers = msg.split()
                words = []
                for line in tickers: words += [w for w in line.split() if w.startswith('(')]
                for d in range(len(words)):
                        words[d] = "".join(c for c in words[d] if c.isalnum())
                ticker = words[0]
                for d in range(len(words)):
                        words[d] = "".join(c for c in words[d] if c.isalnum())
                if(data.lower().find('megadrop') >= 0 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥🔥🔥 Binance announced " + tag + " Megadrop! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                if(data.lower().find('launchpad') >= 0 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥🔥🔥 Binance announced " + tag + " token sale! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                if(data.lower().find('launchpool') >= 0 and duplicate_check('binlist',ticker) == False):
                    tag = ticker_improve(ticker)
                    final = "🔥🔥🔥 Binance announced " + tag + " farm! ([link]("+str(hyperlink)+"?ref=JAO4CT0D) / [pair](https://www.binance.com/en/trade/"+str(ticker.upper())+"_USDT?ref=JAO4CT0D))\n\n@rickler_alerts"
                sender(final, False)
            else:print('Binance filtered')
        elif(msg.lower().find('upbit')>=0):
            data = msg
            for url_entity, _ in hypers.get_entities_text(MessageEntityTextUrl):
                hyperlink = url_entity.url
            #msg = '[거래] KRW 마켓 디지털 자산 추가 (MSK)'
            #msg = '거래 KRW, BTC 마켓 디지털 자산 추가 (SXL, MTTIC)'
            if (data.lower().find('krw') >= 0 or data.lower().find('btc') >= 0 or data.lower().find('usdt') >= 0):
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
                    if (words[x].find('UPBIT') > -1):del_index = [x] + del_index
                    if (words[x].find('LISTING') > -1):del_index = [x] + del_index
                    if (words[x].find('USDT') > -1):
                        del_index = [x] + del_index
                        btc = True
                for z in range(len(del_index)):  # удаляем лишние тикеры
                    words.pop(del_index[z])
                pair_ticker = ''
                print(words)
                if (len(words) == 1):
                    ticker = words[0]
                    if(krw == True):pair_ticker='KRW' #🔥  🔥 🔥 🔥 
                    if(btc == True):pair_ticker='BTC' #last_id replace with hyperlink
                    if(duplicate_check('upbit',words[0]+pair_ticker) == False):
                        tag = ticker_improve(ticker)
                        final = "🔥 Upbit lists " + tag + " ([link](" + str(
                            hyperlink) + ") / [pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) +"-" + str(
                            ticker.upper()) + "))\n\n@rickler_alerts"
                        added += 1
                    else:print('Upbit duplicate')
                elif (len(words) > 1):
                    final = "🔥🔥🔥 Upbit lists "+str(len(words))+" tokens ([link]("+str(hyperlink)+')):\n\n'
                    if (krw == True and btc == False):
                        pair_ticker = 'KRW'
                        for h in range(len(words)):
                            if(duplicate_check('upbit',words[h]+pair_ticker) == False):
                                tag = ticker_improve(words[h])
                                final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) +"-" + str(words[h].upper()) + "))\n"
                                added += 1
                            else:print('Upbit duplicate')
                    if (btc == True and krw == False):
                        pair_ticker = 'BTC'
                        for h in range(len(words)):
                            if(duplicate_check('upbit',words[h]+pair_ticker) == False):
                                tag = ticker_improve(words[h])
                                final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) + "-" + str(words[h].upper()) + "))\n"
                                added += 1
                            else:print('Upbit duplicate')
                    if (krw == True and btc == True):
                        pair_ticker = 'KRW'
                        if(duplicate_check('upbit',words[0]+pair_ticker) == False):
                            tag = ticker_improve(words[0])
                            final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) + "-" + str(words[0].upper()) + "))\n"
                            added += 1
                        else:print('Upbit duplicate')
                        pair_ticker = 'BTC'
                        for h in range(1,len(words)):
                            if(duplicate_check('upbit',words[h]+pair_ticker) == False):
                                tag = ticker_improve(words[h])
                                final = final + tag + " ([pair](https://upbit.com/exchange?code=CRIX.UPBIT." + str(pair_ticker) + "-" + str(words[h].upper()) + "))\n"
                                added += 1
                            else:print('Upbit duplicate')
                    final = final + "\n@rickler_alerts"
                if(len(final)>0 and added > 0):
                    sender(final, False)
                else:print('Upbit IFELSE error or duplicate')
        else:log('coin_listing inside filtered')
    else:log('coin_listing filtered')

def bithumb(data):
    if True:
        if (data.lower().find('원화 마켓') >= 0 or data.lower().find('마켓 추가') >= 0):
            tickers = data.split()
            words = []
            del_index = []
            final=''
            hyper='https://feed.bithumb.com/notice/'
            if(data.find('https')!=0):
                hyper=data[data.find('https'):]
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
                final = "🔥 Bithumb lists " + tag + " ([link](" + str(
                    hyper) + ") / [pair](https://www.bithumb.com/react/trade/order/" + str(
                    ticker.upper()) + "-KRW))\n\n@rickler_alerts"
            elif (len(words) > 1):
                final = "🔥🔥🔥 Bithumb lists "+str(len(words))+" tokens ([link]("+str(hyper)+')):\n\n'
                for h in range(len(words)):
                    tag = ticker_improve(words[h])
                    final = final + tag + " ([pair](https://www.bithumb.com/react/trade/order/" + str(words[h].upper()) + "-KRW))\n"
                final = final + "\n@rickler_alerts"
            if(len(final)>0):sender(final,False)
            else:log('Bithumb IFELSE error or duplicate')
        else:log(' Bithumb filtered!')

#while(True):forwarder() - если нужно поймать ошибку во время написания обновы 
log('started')
# Скрипт постоянно вызывает forwarder(); если возникает ошибка, она логируется и цикл продолжается.
while(True):
    try:forwarder()
    except Exception as e:
        if(errors<100):
            log('global error #' + str(errors) + ' ' + str(e))
            errors += 1
        else:print(errors)
