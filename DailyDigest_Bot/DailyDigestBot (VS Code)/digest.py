# Формирование персонализированного дайджеста

from datetime import datetime
from sources import get_news_for_category, CATEGORIES_DISPLAY

def get_daily_digest(user_categories):
    all_news = []
    for cat in user_categories:
        all_news.extend(get_news_for_category(cat, hours=18))

    seen = set()
    unique = []
    for n in all_news:
        if n["link"] not in seen:
            seen.add(n["link"])
            unique.append(n)

    unique.sort(key=lambda x: x["published"], reverse=True)
    top12 = unique[:12]

    lines = [f"<b>DailyDigest AI</b>\n{datetime.now().strftime('%d.%m.%Y в %H:%M')} МСК\n"]
    for i, item in enumerate(top12, 1):
        t = item["published"].strftime("%H:%M")
        lines.append(
            f"{i}. <b>{item['title']}</b>\n"
            f"{CATEGORIES_DISPLAY.get(item['category'], item['category'])} · {t} · {item['source']}\n"
            f"<a href='{item['link']}'>Читать полностью</a>\n"
        )
    return "\n".join(lines)