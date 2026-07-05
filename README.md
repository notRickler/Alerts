# Rickler Alerts

Rickler Alerts was a crypto listing alerts aggregator that monitored new token listing announcements from exchange websites and Telegram announcement channels, converted them into a unified alert format, and published them to the Rickler Alerts Telegram channel.

The project is now sunset and is being published as an archive of the original working scripts. The code is intentionally simple and mostly procedural, which may make it useful for beginners who want to study how basic parsing, filtering, deduplication, and Telegram alert publishing can work in practice.

This repository is not intended to be a polished production-ready framework. It is a working legacy project that can be improved, refactored, or used as a starting point by anyone interested in maintaining or rebuilding similar listing alerts.

## Files

### `web2.py`

Main web parser script.

It checks exchange websites and public API endpoints for new listing announcements, parses tickers from announcement titles/pages, filters duplicates, updates listing statistics, and sends formatted alerts to Telegram.

The script includes web-source logic for exchanges such as Binance, Upbit, OKX, HTX, Kraken, Bitfinex, Bithumb, and MEXC-related web alerts.

### `telegram.py`

Main Telegram parser script.

It reads selected Telegram announcement channels, checks unread messages, filters potentially relevant listing posts, parses tickers depending on the source channel, checks duplicates, updates statistics, and sends alerts to the Rickler Alerts channel.

This script contains most of the Telegram-source parsing logic for exchanges and listing-related channels.

### `mexc.py`

MEXC delayed sender / buffer script.

MEXC can publish several listing announcements close to each other. This script collects MEXC listing candidates, waits for a configured time window, and then sends either a single MEXC alert or a combined multi-token alert.

### `weekly.py`

Weekly statistics sender.

It reads listing counters from `data.ini`, builds a weekly summary message, sends it to Telegram, saves the current weekly total as `last_week`, and resets the counters for the next week.

### `proxy-test.py`

Simple proxy checker.

It tests proxies from the proxy list file and prints whether each proxy works or fails for the selected test URL.

### `data.ini`

Statistics storage file.

It stores per-exchange listing counters and the previous week’s total. The parser scripts update this file when a new non-duplicate listing is detected.

### `duplicates.txt`

Duplicate storage file.

It stores exchange/ticker pairs that were already processed. This helps prevent repeated alerts when the same token appears multiple times from the same source.

Some exchanges use several internal duplicate keys. For example, Coinbase-related alerts may use keys such as `coinbaselist`, `coinbaseroad`, or `coinlistings`, while Upbit alerts may include pair-specific keys such as `PENGUBTC` or `PENGUKRW`.

### `collected.txt`

Temporary MEXC collection file.

It is used by the MEXC flow to store listing candidates before `mexc.py` sends a combined alert. The first line stores the collection start timestamp, and the following lines store announcement IDs and tickers in pairs.

### `proxyS.txt`

Proxy list file.

Used by the scripts for network requests through proxies.

`web2.py` makes frequent requests to exchange websites and public endpoints. To reduce the risk of IP bans caused by repeated requests, it is recommended to use a proxy pool of around **100–150 proxies**.

Add your proxies to `proxyS.txt`, one proxy per line.

## Requirements

Install the required third-party libraries before running the scripts:

```bash
pip install -r requirements.txt
```

Or install them manually:

```bash
pip install telethon "requests[socks]" beautifulsoup4 demoji
```

The main external libraries are:

- `telethon` — Telegram client library used to read Telegram channels and send alerts.
- `requests` — HTTP requests for web/API parsing.
- `requests[socks]` / `PySocks` — SOCKS proxy support for `requests`.
- `beautifulsoup4` — HTML parsing for web pages.
- `demoji` — emoji cleanup in Telegram messages.

Built-in Python modules such as `json`, `time`, `datetime`, `random`, `re`, and `configparser` do not need to be installed separately.

## Setup

Before running the scripts, replace placeholder values with your own Telegram API credentials and Telegram destinations:

```python
api_id = 123456
api_hash = 'your_api_hash'

# Куда отправлять служебные уведомления о запуске и ошибках.
ADMIN_CHAT = 'your_admin_username_or_id'

# Канал, куда публикуются готовые алерты о листингах.
ALERTS_CHANNEL = 'your_alerts_channel_username_or_id'
```

You can get `api_id` and `api_hash` from Telegram:

1. Go to `https://my.telegram.org`.
2. Click under **API Development tools**.
3. A **Create new application** window will appear.
4. Fill in your application details.
5. There is no need to enter any URL.
6. Only the first two fields, **App title** and **Short name**, can currently be changed later.
7. Click **Create application** at the end.

Remember that your API hash is secret and Telegram will not let you revoke it. Do not post it anywhere.

You also need to configure your Telegram session, source channels, proxy list, and any source-specific settings required for your environment.

The scripts assume that supporting files such as `data.ini`, `duplicates.txt`, `collected.txt`, and `proxyS.txt` exist in the same working directory.

## Notes

Rickler Alerts was originally built to be fast enough for practical listing alerts, not to be an ideal software architecture example.

The code uses direct parsing logic, long conditional blocks, simple text files for state, and straightforward Telegram publishing. This makes it easier to understand, but also leaves many opportunities for optimization and refactoring.

### Code comments

Rickler Alerts was most popular in the CIS region, so the code comments are written in Russian.

## TODO

### Globally: Telegram & Web

- Port all scripts to a faster programming language.
- Make parsing parallel for every source/exchange, or split scripts into separate parsers for each source.
- Use low-latency servers located close to each source.
- Find a faster source for Binance listing announcements.
- Replace long `if` chains with dispatch mappings.
- Add atomic writing for `data.ini` and `duplicates.txt`.

### Telegram Alerts

- Integrate AI-based filtering and parsing.

### Web Alerts

- Add a `sender()` function similar to the Telegram script.
- Add protection for empty lists and missing parser results.
- Find an alternative way to parse Bithumb `buildId`, or find an alternative way to parse Bithumb announcements.

## Sunset Notice

Rickler Alerts is no longer actively maintained.

Initially, the channel was one of the only working crypto listing aggregators, but the ecosystem has changed and there are now enough alternative tools available. The original scripts are published here for transparency, educational purposes, and for anyone who may want to continue or rebuild the project.

Thank you to everyone who followed and supported Rickler Alerts.
