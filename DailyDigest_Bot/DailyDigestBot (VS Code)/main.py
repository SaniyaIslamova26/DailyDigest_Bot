# main.py

import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramBadRequest

session = AiohttpSession(timeout=180.0)

import config
from db import init_db, add_user, update_categories, get_user_categories, get_all_subscribers, unsubscribe_user
from scheduler import start_scheduler
from digest import get_daily_digest
from sources import CATEGORIES_DISPLAY

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN, session=session)
dp = Dispatcher(storage=MemoryStorage())
ADMIN_ID = config.ADMIN_ID


class States(StatesGroup):
    choosing = State()


def main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Мои категории"), KeyboardButton(text="Дайджест сейчас")],
        [KeyboardButton(text="Ещё 10 новостей"), KeyboardButton(text="Реферальная ссылка")],
        [KeyboardButton(text="Отписаться")]
    ]
    if user_id == ADMIN_ID:
        kb.append([KeyboardButton(text="Статистика")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def categories_keyboard(selected: list) -> InlineKeyboardMarkup:
    kb = []
    for code, name in CATEGORIES_DISPLAY.items():
        mark = "✓" if code in selected else "⬜"
        kb.append([InlineKeyboardButton(text=f"{mark} {name}", callback_data=f"cat_{code}")])
    kb.append([InlineKeyboardButton(text="Сохранить", callback_data="save")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    init_db()
    user_id = message.from_user.id
    add_user(user_id)

    ref_link = f"https://t.me/DailyDigestAI_Bot?start=ref_{user_id}"

    await message.answer(
        "DailyDigest AI\n\n"
        "Персональный политический дайджест из 85+ СМИ России\n\n"
        "• 8 тематических категорий\n"
        "• 12 главных новостей ежедневно\n"
        "• Безлимит по реферальной ссылке\n\n"
        f"Ваша ссылка:\n{ref_link}\n"
        "Пришлите другу — оба получите 7 дней без лимита!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Поделиться ссылкой", url=f"https://t.me/share/url?url={ref_link}")
        ]])
    )

    cats = get_user_categories(user_id)
    await state.set_state(States.choosing)
    await state.update_data(selected=cats or [])
    await message.answer("Выберите интересующие темы:", reply_markup=categories_keyboard(cats))


@dp.callback_query(lambda c: c.data and c.data.startswith("cat_"))
async def toggle(callback: types.CallbackQuery, state: FSMContext):
    cat = callback.data[4:]
    data = await state.get_data()
    selected = data.get("selected", [])
    if cat in selected:
        selected.remove(cat)
    else:
        selected.append(cat)
    await state.update_data(selected=selected)
    try:
        await callback.message.edit_reply_markup(reply_markup=categories_keyboard(selected))
    except TelegramBadRequest:
        pass
    await callback.answer()


@dp.callback_query(lambda c: c.data == "save")
async def save(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])
    update_categories(callback.from_user.id, selected)
    await state.clear()

    await callback.message.edit_text(f"Категории сохранены! Выбрано: {len(selected)}")
    await callback.message.answer("Меню:", reply_markup=main_keyboard(callback.from_user.id))
    await callback.answer("Готово!")


@dp.message(lambda m: m.text == "Мои категории")
async def my_cats(message: types.Message, state: FSMContext):
    cats = get_user_categories(message.from_user.id)
    await state.set_state(States.choosing)
    await state.update_data(selected=cats)
    await message.answer("Изменить категории:", reply_markup=categories_keyboard(cats))


@dp.message(lambda m: m.text == "Дайджест сейчас")
async def digest_now(message: types.Message):
    cats = get_user_categories(message.from_user.id)
    if not cats:
        await message.answer("Сначала выберите категории")
        return
    msg = await message.answer("Формирую дайджест...")
    text = get_daily_digest(cats)
    await msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)


@dp.message(lambda m: m.text == "Ещё 10 новостей")
async def more(message: types.Message):
    cats = get_user_categories(message.from_user.id)
    if not cats:
        await message.answer("Сначала выберите категории")
        return
    from sources import get_news_for_category
    all_news = []
    for cat in cats:
        all_news.extend(get_news_for_category(cat, hours=48))
    seen = set()
    unique = [n for n in all_news if n["link"] not in seen and not seen.add(n["link"])]
    unique.sort(key=lambda x: x["published"], reverse=True)
    extra = unique[12:22]
    if not extra:
        await message.answer("Больше новостей нет")
        return
    lines = ["<b>Ещё 10 новостей:</b>\n"]
    for i, item in enumerate(extra, 13):
        lines.append(
            f"{i}. <b>{item['title']}</b>\n"
            f"{CATEGORIES_DISPLAY.get(item['category'], '')} · {item['published'].strftime('%H:%M')}\n"
            f"<a href='{item['link']}'>Читать</a>\n"
        )
    await message.answer("\n".join(lines), parse_mode="HTML", disable_web_page_preview=True)


@dp.message(lambda m: m.text == "Реферальная ссылка")
async def ref(message: types.Message):
    link = f"https://t.me/DailyDigestAI_Bot?start=ref_{message.from_user.id}"
    await message.answer(f"<b>Ваша ссылка:</b>\n<code>{link}</code>", parse_mode="HTML",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                             InlineKeyboardButton(text="Поделиться", url=f"https://t.me/share/url?url={link}")
                         ]]))


@dp.message(lambda m: m.text == "Отписаться")
async def unsub(message: types.Message):
    unsubscribe_user(message.from_user.id)
    await message.answer("Вы отписаны. Чтобы вернуться — /start")


@dp.message(lambda m: m.text == "Статистика")
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    subs = len(get_all_subscribers())
    from collections import Counter
    popular = Counter()
    for uid in get_all_subscribers():
        popular.update(get_user_categories(uid))
    text = f"<b>СТАТИСТИКА</b>\n\nПодписчиков: <b>{subs}</b>\n\n<b>Популярные категории:</b>\n"
    for cat, cnt in popular.most_common():
        text += f"• {CATEGORIES_DISPLAY.get(cat, cat)} — {cnt} чел.\n"
    await message.answer(text, parse_mode="HTML")


async def on_startup(_):
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущен!")


async def main():
    init_db()
    start_scheduler(bot)
    await dp.start_polling(bot, on_startup=on_startup)


if __name__ == "__main__":
    asyncio.run(main())