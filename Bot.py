import asyncio
import re
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Filter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = ""

ALLOWED_USERNAMES = []

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_stats = {}

class IsWhitelisted(Filter):
    async def __call__(self, message: types.Message) -> bool:
        if message.from_user.username and message.from_user.username in ALLOWED_USERNAMES:
            return True
        return False

def get_main_menu():
    kb = [
        [KeyboardButton(text="👤 Профіль")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def extract_tiktok_url(text: str) -> str | None:
    if not text:
        return None
    pattern = r'(https?://(?:www\.|vt\.|vm\.)?tiktok\.com/.*)'
    match = re.search(pattern, text)
    return match.group(0) if match else None

async def get_tiktok_video(url: str) -> str | None:
    api_url = "https://tikwm.com/api/"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url, params={'url': url}) as response:
                data = await response.json()
                if data.get('code') == 0:
                    return data['data']['play']
                return None
        except Exception as e:
            print(f"Помилка API: {e}")
            return None

@dp.message(Command("start"), IsWhitelisted())
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_stats:
        user_stats[user_id] = 0

    await message.answer(
        "Привіт! 👋\n"
        "Надішли мені посилання на відео з TikTok, і я завантажу його без водяного знака.",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "👤 Профіль", IsWhitelisted())
async def profile_cmd(message: types.Message):
    user_id = message.from_user.id
    count = user_stats.get(user_id, 0)
    username = f"@{message.from_user.username}"
    
    profile_text = (
        f"👤 <b>Ваш профіль</b>\n"
        f"├ <b>Юзернейм:</b> {username}\n"
        f"└ <b>Завантажено відео:</b> {count} шт."
    )
    
    await message.answer(profile_text, parse_mode="HTML")

@dp.message(F.text, IsWhitelisted())
async def handle_tiktok_link(message: types.Message):
    url = extract_tiktok_url(message.text)
    
    if not url:
        await message.answer("Будь ласка, надішліть коректне посилання на TikTok.")
        return

    wait_msg = await message.answer("⏳ Шукаю та завантажую відео, зачекайте трішки...")
    video_url = await get_tiktok_video(url)

    if video_url:
        try:
            await message.reply_video(
                video=video_url,
                caption="✨ <b>Дякуємо за використання нашого бота!</b>",
                parse_mode="HTML"
            )
            await wait_msg.delete()
            
            user_id = message.from_user.id
            user_stats[user_id] = user_stats.get(user_id, 0) + 1
            
        except Exception as e:
            print(f"Помилка відправки відео: {e}")
            await wait_msg.edit_text("❌ Сталася помилка при відправці відео. Можливо, воно завелике.")
    else:
        await wait_msg.edit_text("❌ Не вдалося отримати відео. Перевірте посилання або спробуйте пізніше.")


@dp.message()
async def access_denied(message: types.Message):
    await message.answer("❌ Помилка доступу: у вас немає дозволу на використання цього бота.")

async def main():
    print("Бот запущений...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())