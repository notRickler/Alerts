import requests

# Простой скрипт для проверки proxy из proxySD.txt: делает тестовый запрос и печатает OK/FAIL.
#test_url = "http://google.com"
test_url = "http://discord.com"
timeout = 5

# Каждый proxy используется и для http, и для https-запросов.
with open("proxySD.txt") as f:
    for p in f:
        proxy = p.strip()
        if not proxy:
            continue

        proxies = {
            "http": proxy,
            "https": proxy
        }

        try:
            r = requests.get(test_url, proxies=proxies, timeout=timeout)
            print("OK ", proxy) if r.status_code == 200 else print("FAIL", proxy)
        except:
            print("FAIL", proxy)
