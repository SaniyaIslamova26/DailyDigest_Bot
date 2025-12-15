# sources.py
import feedparser
import re
from datetime import datetime, timedelta

CATEGORIES_DISPLAY = {
    "pol_rf": "Политика РФ",
    "int": "Международная политика",
    "econ": "Экономика и финансы",
    "tech": "Технологии и IT",
    "society": "Общество",
    "defense": "Оборона и безопасность",
    "regions": "Регионы России",
    "culture": "Культура и наука"
}

# 85+ RSS-лент из топ-100 российских СМИ
RSS_FEEDS = {
    "pol_rf": [
        "https://ria.ru/export/rss2/politics/index.xml",
        "https://tass.ru/rss/v2.xml",
        "https://lenta.ru/rss/news/russia",
        "https://rg.ru/xml/index.xml",
        "https://www.gazeta.ru/export/rss/politics.xml",
        "https://iz.ru/xml/rss/all.xml",
        "https://www.kp.ru/rss/politics.xml",
        "https://www.1tv.ru/news/politics/rss",
        "https://www.rbc.ru/rssfeed/news/politics",
        "https://www.kommersant.ru/rss/politics.xml",
        "https://www.vesti.ru/rss/politics",
        "https://smotrim.ru/rss",
    ],
    "int": [
        "https://ria.ru/export/rss2/world/index.xml",
        "https://lenta.ru/rss/news/world",
        "https://www.bbc.com/russian/rss.xml",
        "https://tass.ru/mezhdunarodnaya-panorama/rss",
        "https://www.dw.com/ru/rss",
        "https://inosmi.ru/export/rss.xml",
        "https://www.rbc.ru/story/rss",
    ],
    "econ": [
        "https://ria.ru/export/rss2/economy/index.xml",
        "https://www.rbc.ru/rssfeed/news/economics",
        "https://www.vedomosti.ru/rss/news",
        "https://www.kommersant.ru/RSS/news.xml",
        "https://www.forbes.ru/rss",
        "https://www.banki.ru/rss/news/",
        "https://finam.ru/rss/news.xml",
        "https://www.interfax.ru/rss.asp",
    ],
    "tech": [
        "https://hi-tech.mail.ru/rss/all/",
        "https://habr.com/ru/rss/best/daily/",
        "https://3dnews.ru/rss/",
        "https://www.cnews.ru/rss/news.xml",
        "https://www.ixbt.com/export/news.rss",
        "https://tproger.ru/feed/",
        "https://rozetked.me/rss",
        "https://vc.ru/rss",
        "https://nplus1.ru/rss",
    ],
    "society": [
        "https://ria.ru/export/rss2/society/index.xml",
        "https://lenta.ru/rss/news/society",
        "https://www.fontanka.ru/fontanka.rss",
        "https://www.mk.ru/rss/social/",
        "https://life.ru/rss",
        "https://www.gazeta.ru/social/rss",
        "https://www.interfax.ru/rss.asp",
    ],
    "defense": [
        "https://ria.ru/export/rss2/defense_safety/index.xml",
        "https://tass.ru/armiya-i-opk/rss",
        "https://zvezdaweekly.ru/news/rss",
        "https://topwar.ru/rss.xml",
        "https://rg.ru/rss/defense.xml",
    ],
    "regions": [
        "https://ria.ru/export/rss2/regions/index.xml",
        "https://ura.news/rss",
        "https://tass.ru/regions/rss",
        "https://74.ru/rss/",
        "https://kuban24.tv/rss",
        "https://ngs.ru/rss/",
        "https://e1.ru/rss/",
    ],
    "culture": [
        "https://ria.ru/export/rss2/culture/index.xml",
        "https://www.culture.ru/rss/news",
        "https://rg.ru/rss/rg/culture.xml",
        "https://nplus1.ru/rss",
        "https://www.afisha.ru/rss/",
        "https://kudago.com/rss",
        "https://tass.ru/kultura/rss",
    ]
}

KEYWORDS = {
    "pol_rf": ["правительство", "госдума", "кремль", "путин", "закон", "выборы", "медведев"],
    "int": ["сша", "китай", "украина", "нато", "оон", "санкции", "трамп", "си цзиньпин"],
    "econ": ["рубль", "доллар", "цб", "инфляция", "нефть", "газпром", "ввп", "ставка"],
    "tech": ["ии", "нейросеть", "смартфон", "гаджет", "чип", "программирование", "стартап"],
    "society": ["здравоохранение", "образование", "дтп", "происшествие", "погода", "мчс", "пенсия"],
    "defense": ["армия", "вс рф", "спецоперация", "оружие", "танк", "гиперзвук"],
    "regions": ["москва", "петербург", "татарстан", "сибирь", "дальний восток", "крым"],
    "culture": ["музей", "театр", "кино", "наука", "космос", "роскосмос", "фестиваль"]
}

def clean_text(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text).strip()

def parse_rss(url: str):
    try:
        feed = feedparser.parse(url, request_headers={'User-Agent': 'DailyDigestAI/3.0'})
        entries = []
        for item in feed.entries[:30]:
            pub = item.get("published_parsed") or item.get("updated_parsed")
            pub_date = datetime(*pub[:6]) if pub else datetime.now()
            entries.append({
                "title": clean_text(item.title),
                "summary": clean_text(item.get("summary", "")),
                "link": item.link,
                "published": pub_date,
                "source": feed.feed.get("title", "Источник")
            })
        return entries
    except:
        return []

def get_news_for_category(category: str, hours: int = 36):
    cutoff = datetime.now() - timedelta(hours=hours)
    result = []
    for url in RSS_FEEDS.get(category, []):
        for item in parse_rss(url):
            if item["published"] >= cutoff:
                text = (item["title"] + " " + item["summary"]).lower()
                if any(kw in text for kw in KEYWORDS.get(category, [])):
                    item["category"] = category
                    result.append(item)
    result.sort(key=lambda x: x["published"], reverse=True)
    return result[:40]  

def get_news_stats(hours: int = 24) -> dict:
    """Возвращает количество новостей по категориям за последние N часов"""
    stats = {cat: 0 for cat in CATEGORIES_DISPLAY}
    cutoff = datetime.now() - timedelta(hours=hours)
    seen_links = set()

    for cat, urls in RSS_FEEDS.items():
        for url in urls:
            for item in parse_rss(url):
                if item["link"] in seen_links:
                    continue
                if item["published"] >= cutoff:
                    text = (item["title"] + " " + item["summary"]).lower()
                    if any(kw in text for kw in KEYWORDS.get(cat, [])):
                        stats[cat] += 1
                        seen_links.add(item["link"])
    return stats