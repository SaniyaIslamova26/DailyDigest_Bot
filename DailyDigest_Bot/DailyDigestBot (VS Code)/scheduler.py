# Планировщик автоматической ежедневной рассылки

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
from aiogram import Bot
from db import get_all_subscribers, get_user_categories
from digest import get_daily_digest
import asyncio
from datetime import date

MOSCOM_TZ = pytz.timezone('Europe/Moscow')
last_sent = {}

async def send_daily_digest(bot: Bot):
    """Рассылка дайджеста всем подписчикам"""
    today = date.today()
    for user_id in get_all_subscribers():
        if last_sent.get(user_id) == today:
            continue
        try:
            text = get_daily_digest(get_user_categories(user_id))
            await bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=True)
            last_sent[user_id] = today
            await asyncio.sleep(0.33)
        except Exception as e:
            print(f"Ошибка отправки {user_id}: {e}")

def start_scheduler(bot: Bot):
    """Запуск планировщика на 9:00 МСК ежедневно"""
    scheduler = AsyncIOScheduler(timezone=MOSCOM_TZ)
    scheduler.add_job(send_daily_digest, "cron", hour=9, minute=0, args=(bot,)) 
    scheduler.start()
    print("📅 Планировщик запущен — рассылка каждый день в 9:00 МСК")