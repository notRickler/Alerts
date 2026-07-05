from telethon.sync import TelegramClient
from datetime import datetime
import time
import configparser

# Данные Telegram API вынесены в переменные, чтобы их можно было заменить перед запуском.
api_id = 123456
api_hash = 'your_api_hash'

# Кому в Telegram отправлять служебные уведомления о запуске и ошибках.
# Можно указать как канал, так и пользователя, без @
ADMIN_CHAT = 'username'

# Канал Telegram, куда публикуются готовые алерты о листингах.
# Можно указать как канал, так и пользователя, без @
ALERTS_CHANNEL = 'channel_username'

def times():
    return datetime.now().strftime('[%H:%M:%S.%f')[:-3]+str(']')

print(times(),'started!')

def loopy():
    # Скрипт раз в неделю собирает статистику из data.ini, отправляет отчёт и сбрасывает счётчики.
    with TelegramClient("AlertsMexc", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
        client.send_message(ADMIN_CHAT, 'Weekly started!', silent=True)
        client.disconnect()
    while True:
        time.sleep(1)
        hour = datetime.now().strftime('%H')
        minute = datetime.now().strftime('%M')
        day = datetime.now().weekday() # 6 == Sunday
        # Sunday 20:00 — момент отправки weekly-статистики.
        if(day==6 and hour=='20' and minute=='00'): 
            config = configparser.ConfigParser(strict=False)
            config.read("data.ini")
            final='**#Weekly listings statistics!** 📊\n\n'
            if(config['Listings']['binance']!='0'):final=final+"🔥 Binance - "+config['Listings']['binance']+"\n"
            if(config['Listings']['bithumb']!='0'):final=final+"🔥 Bithumb - "+config['Listings']['bithumb']+"\n"
            if(config['Listings']['bybit']!='0'):final=final+"🔥 Bybit - "+config['Listings']['bybit']+"\n"
            if(config['Listings']['coinbase']!='0'):final=final+"🔥 Coinbase - "+config['Listings']['coinbase']+"\n"
            if(config['Listings']['upbit']!='0'):final=final+"🔥 Upbit - "+config['Listings']['upbit']+"\n"
            if(config['Listings']['okx']!='0'):final=final+"🔥 OKX - "+config['Listings']['okx']+"\n"
            if(config['Listings']['robinhood']!='0'):final=final+"🔥 Robinhood - "+config['Listings']['robinhood']+"\n"
            if(config['Listings']['binance']!='0' or config['Listings']['bithumb']!='0' or config['Listings']['coinbase']!='0' or config['Listings']['okx']!='0' or config['Listings']['upbit']!='0' or config['Listings']['bybit']!='0' or config['Listings']['robinhood']!='0'):final=final+"\n"
            if(config['Listings']['ascendex']!='0'):final=final+"AscendEX - "+config['Listings']['ascendex']+"\n"
            if(config['Listings']['bitfinex']!='0'):final=final+"Bitfinex - "+config['Listings']['bitfinex']+"\n"
            if(config['Listings']['bingx']!='0'):final=final+"BingX - "+config['Listings']['bingx']+"\n"
            if(config['Listings']['bitget']!='0'):final=final+"Bitget - "+config['Listings']['bitget']+"\n"
            if(config['Listings']['coinlist']!='0'):final=final+"CoinList - "+config['Listings']['coinlist']+"\n"
            if(config['Listings']['cryptocom']!='0'):final=final+"CryptoCom - "+config['Listings']['cryptocom']+"\n"
            if(config['Listings']['gate']!='0'):final=final+"Gate - "+config['Listings']['gate']+"\n"
            if(config['Listings']['kraken']!='0'):final=final+"Kraken - "+config['Listings']['kraken']+"\n"
            if(config['Listings']['kucoin']!='0'):final=final+"KuCoin - "+config['Listings']['kucoin']+"\n"
            if(config['Listings']['htx']!='0'):final=final+"HTX - "+config['Listings']['htx']+"\n"
            if(config['Listings']['mexc']!='0'):final=final+"MEXC - "+config['Listings']['mexc']+"\n"
            # Считаем общий итог по всем биржам, затем обнуляем недельные счётчики.
            total = 0
            for i in config['Listings']:
                total = total + int(config['Listings'][i])
            for i in config['Listings']:
                config['Listings'][i]="0"
            final = final + f"\nTotal {total} this week, {config['Dates']['last_week']} last week"
            final = final + '\n\n@rickler_alerts'
            config['Dates']['last_week']=str(total)
            with open('data.ini', 'w') as config_file:
                config.write(config_file)
            with TelegramClient("AlertsMexc", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                client.send_message(ALERTS_CHANNEL, final, link_preview=False,silent=True)
                client.disconnect()
            # Пауза нужна, чтобы отчёт не отправился несколько раз в течение одной и той же минуты.
            time.sleep(68)

try:loopy()
except Exception as e:
    with TelegramClient("AlertsMexc", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
        client.send_message(ADMIN_CHAT, str('Stats error '+str(e)), link_preview=False)
        client.disconnect()
