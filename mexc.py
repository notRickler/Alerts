from telethon.sync import TelegramClient
from datetime import datetime
import time

# Данные Telegram API вынесены в переменные, чтобы не хранить их внутри TelegramClient.
api_id = 123456
api_hash = 'your_api_hash'

# Куда отправлять служебные уведомления о запуске и ошибках.
# Можно указать как канал, так и пользователя, без @
ADMIN_CHAT = 'username'

# Канал, куда публикуются готовые алерты о листингах.
# Можно указать как канал, так и пользователя, без @
ALERTS_CHANNEL = 'channel_username'

# Сколько секунд ждать, прежде чем отправить накопленные MEXC-листинги одним сообщением.
COLLECT_WINDOW_SECONDS = 7200

def times():
    return datetime.now().strftime('[%H:%M:%S.%f')[:-3]+str(']')

print(times(),'started!')

# collected.txt хранит timestamp первой новости, а затем пары: id новости / ticker.
collect = []

def ticker_improve(tick):
    if any(char.isdigit() for char in tick) or len(tick)>8:res = str('''#''')+str(tick)
    else:res = str('$')+str(tick)
    res = res.upper()
    return res

def differ():
    # Проверяем, прошло ли достаточно времени с первой накопленной MEXC-новости.
    global collect
    with open('collected.txt', 'r') as file:
        collect = [line.strip() for line in file]
    if(len(collect)>1):difference = time.time() - float(collect[0])
    else: return False
    if(difference > COLLECT_WINDOW_SECONDS):return True
    else: return False

def looppy():
    # Основной цикл: ждём либо истечения таймера, либо накопления нескольких токенов.
    global collect
    with TelegramClient("AlertsMexc", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
        client.send_message(ADMIN_CHAT, 'Mexc started!', silent=True)
        client.disconnect()
    while True:
        time.sleep(1)
        check = differ()
        if(len(collect)>1):
            # Если окно ожидания закончилось, отправляем всё, что успело накопиться.
            if(len(collect)>=2 and check==True):
                with open('collected.txt', 'r+') as f:
                    f.truncate()
                if(len(collect)==3):
                    tag = ticker_improve(collect[2])
                    final = "MEXC lists " + tag + " ([link](https://www.mexc.com/support/articles/" + str(collect[1]) + ") / [pair](https://www.mexc.com/exchange/"+str(collect[2])+"_USDT))\n\n@rickler_alerts"
                else:
                    final = "MEXC lists "+str(int((len(collect)-1)/2))+" tokens:\n\n"
                    for h in range(1,len(collect)-1,2):
                        tag = ticker_improve(collect[h+1])
                        final = final + tag + " ([link](https://www.mexc.com/support/articles/" + str(collect[h]) + ") / [pair](https://www.mexc.com/exchange/"+str(collect[h+1])+"_USDT))\n"
                    final = final + "\n@rickler_alerts"
                with TelegramClient("AlertsMexc", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                    client.send_message(ALERTS_CHANNEL, final, link_preview=False,silent=True)
                    client.disconnect()
                print(times(),'sent timer')
            # Если токенов накопилось много, отправляем сообщение раньше таймера.
            elif(len(collect)>6):
                with open('collected.txt', 'r+') as f:
                    f.truncate()
                final = "MEXC lists "+str(int((len(collect)-1)/2))+" tokens:\n\n"
                for h in range(1,len(collect)-1,2):
                    tag = ticker_improve(collect[h+1])
                    final = final + tag + " ([link](https://www.mexc.com/support/articles/" + str(collect[h]) + ") / [pair](https://www.mexc.com/exchange/"+str(collect[h+1])+"_USDT))\n"
                final = final + "\n@rickler_alerts"
                with TelegramClient("AlertsMexc", api_id, api_hash, system_version="Windows 10CUSTOM") as client:
                    client.send_message(ALERTS_CHANNEL, final, link_preview=False,silent=True)
                    client.disconnect()
                print(times(),'sent 3+')

try:looppy()
except Exception as e:print(times(),e)
