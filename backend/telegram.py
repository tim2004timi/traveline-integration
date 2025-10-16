import asyncio
import logging
from minio import Minio
from minio.error import S3Error
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command, StateFilter
from config import Settings
from service import (
    get_feedbacks,
    create_feedback,
    delete_feedback,
    get_video_feedbacks,
    create_video_feedback,
    delete_video_feedback,
    get_video_feedback_by_uuid,
)
from schemas import FeedbackCreate, VideoFeedbackCreate
import io
import uuid as uuid_lib

settings = Settings()
logger = logging.getLogger(__name__)

# --- FSM ---
class FeedbackStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_rate = State()

# --- FSM (video) ---
class VideoStates(StatesGroup):
    waiting_for_file = State()

# --- MinIO ---
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)

# --- Bot/Dispatcher ---
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# --- Helpers ---

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids_list

async def init_minio():
    try:
        if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
            minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
            logger.info("MinIO bucket '%s' создан", settings.MINIO_BUCKET_NAME)
        else:
            logger.info("MinIO bucket '%s' уже существует", settings.MINIO_BUCKET_NAME)
    except S3Error as e:
        logger.error("Ошибка MinIO: %s", e)

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📹 Видео-отзывы", callback_data="video_reviews")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="text_reviews")],
    ])

def get_actions_keyboard(category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Просмотреть", callback_data=f"view_{category}")],
        [InlineKeyboardButton(text="➕ Добавить", callback_data=f"add_{category}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{category}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")],
    ])

def get_rate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}")
            for i in (0, 1, 2)
        ],
        [
            InlineKeyboardButton(text=str(i), callback_data=f"rate_{i}")
            for i in (3, 4, 5)
        ],
    ])

def get_delete_feedbacks_keyboard(feedbacks) -> InlineKeyboardMarkup:
    buttons = []
    for i in range(0, len(feedbacks), 3):
        row = []
        for j in range(3):
            if i + j < len(feedbacks):
                fb = feedbacks[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=str(fb.id),
                        callback_data=f"delete_feedback_{fb.id}",
                    )
                )
        if row:
            buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="text_reviews")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_long_text(message_or_callback, text: str, **kwargs):
    """
    Безопасная отправка/редактирование длинного текста (разбивка по 4096).
    message_or_callback: Message или CallbackQuery
    """
    MAX = 4096
    chunks = [text[i:i+MAX] for i in range(0, len(text), MAX)] or [""]
    # Если это ответ на callback и можно редактировать — редактируем первый кусок,
    # остальное досылаем как новые сообщения
    if isinstance(message_or_callback, CallbackQuery):
        cb = message_or_callback
        try:
            await cb.message.edit_text(chunks[0], **kwargs)
        except Exception:
            await cb.message.answer(chunks[0], **kwargs)
        for chunk in chunks[1:]:
            await cb.message.answer(chunk)
    else:
        msg = message_or_callback
        for i, chunk in enumerate(chunks):
            if i == 0:
                await msg.answer(chunk, **kwargs)
            else:
                await msg.answer(chunk)

# --- Handlers ---

@dp.message(Command("start"))
async def start_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    welcome = "👋 Добро пожаловать в панель администратора!\n\nВыберите нужный раздел:"
    await message.answer(welcome, reply_markup=get_main_menu_keyboard())

@dp.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    welcome = "👋 Добро пожаловать в панель администратора!\n\nВыберите нужный раздел:"
    try:
        await callback.message.edit_text(welcome, reply_markup=get_main_menu_keyboard())
    finally:
        await callback.answer()

@dp.callback_query(F.data == "video_reviews")
async def video_reviews_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    text = "📹 <b>Видео-отзывы</b>\n\nВыберите действие:"
    await callback.message.edit_text(text, reply_markup=get_actions_keyboard("video"))
    await callback.answer()

@dp.callback_query(F.data == "text_reviews")
async def text_reviews_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    text = "⭐ <b>Отзывы</b>\n\nВыберите действие:"
    await callback.message.edit_text(text, reply_markup=get_actions_keyboard("text"))
    await callback.answer()

@dp.callback_query(F.data.startswith("view_"))
async def view_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    category = callback.data.split("_", 1)[1]
    if category == "video":
        videos = await get_video_feedbacks()
        if not videos:
            text = "📹 <b>Просмотр видео-отзывов</b>\n\nВидео-отзывов пока нет."
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard(category))
        else:
            header = "📹 <b>Видео-отзывы</b>\n\nОтправляю доступные видео..."
            try:
                await callback.message.edit_text(header, reply_markup=get_actions_keyboard(category))
            except Exception:
                await callback.message.answer(header, reply_markup=get_actions_keyboard(category))
            # Отправляем каждое видео отдельным сообщением (через загрузку из MinIO)
            for v in videos:
                try:
                    obj = minio_client.get_object(settings.MINIO_BUCKET_NAME, v.file)
                    data = obj.read()
                    obj.close()
                    obj.release_conn()
                    tg_file = BufferedInputFile(data, filename=f"{v.uuid}.mp4")
                    await callback.message.answer_video(video=tg_file, caption=v.uuid)
                except Exception:
                    await callback.message.answer(f"{v.uuid}: не удалось отправить видео")
    else:
        feedbacks = await get_feedbacks()
        if not feedbacks:
            text = "⭐ <b>Просмотр отзывов</b>\n\nОтзывов пока нет."
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard(category))
        else:
            header = "⭐ <b>Просмотр отзывов</b>\n\n"
            body = "\n".join(f"{fb.id}) {fb.text}" for fb in feedbacks)
            await send_long_text(
                callback,
                header + body,
                reply_markup=get_actions_keyboard(category),
            )
    await callback.answer()

@dp.callback_query(F.data.startswith("add_"))
async def add_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    category = callback.data.split("_", 1)[1]
    if category == "video":
        text = "📹 <b>Добавление видео-отзыва</b>\n\nОтправьте видео-файл для добавления."
        await callback.message.edit_text(text)
        await state.set_state(VideoStates.waiting_for_file)
    else:
        text = "⭐ <b>Добавление отзыва</b>\n\nВведите текст отзыва:"
        await callback.message.edit_text(text)
        await state.set_state(FeedbackStates.waiting_for_text)
    await callback.answer()

@dp.callback_query(F.data.in_({"delete_text", "delete_video"}))
async def delete_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    category = callback.data.split("_", 1)[1]  # "text" | "video"
    if category == "video":
        videos = await get_video_feedbacks()
        if not videos:
            text = "📹 <b>Удаление видео-отзыва</b>\n\nВидео-отзывов для удаления нет."
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard(category))
        else:
            text = "📹 <b>Удаление видео-отзыва</b>\n\nВыберите видео (по UUID), которое хотите удалить:"
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=v.uuid, callback_data=f"delete_video_{v.uuid}")
                        for v in videos[i:i+2]
                    ]
                    for i in range(0, len(videos), 2)
                ]
            )
            kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="video_reviews")])
            try:
                await callback.message.edit_text(text, reply_markup=kb)
            except Exception:
                await callback.message.answer(text, reply_markup=kb)
    else:
        feedbacks = await get_feedbacks()
        if not feedbacks:
            text = "⭐ <b>Удаление отзыва</b>\n\nОтзывов для удаления нет."
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard(category))
        else:
            text = "⭐ <b>Удаление отзыва</b>\n\nВыберите отзыв, который хотите удалить:"
            try:
                await callback.message.edit_text(text, reply_markup=get_delete_feedbacks_keyboard(feedbacks))
            except Exception:
                await callback.message.answer(text, reply_markup=get_delete_feedbacks_keyboard(feedbacks))

    await callback.answer()

# --- ВВОД ТЕКСТА ОТЗЫВА (stateful) ---
@dp.message(StateFilter(FeedbackStates.waiting_for_text))
async def process_feedback_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return

    await state.update_data(text=message.text)
    text = "⭐ <b>Добавление отзыва</b>\n\nВыберите оценку:"
    await message.answer(text, reply_markup=get_rate_keyboard())
    await state.set_state(FeedbackStates.waiting_for_rate)

# --- ВВОД ВИДЕО (stateful) ---
@dp.message(StateFilter(VideoStates.waiting_for_file), F.video)
async def process_video_upload(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    try:
        # Скачиваем файл из Telegram в память
        buf = io.BytesIO()
        await message.bot.download(message.video, destination=buf)
        buf.seek(0)

        # Генерируем имя и кладём в MinIO
        uid = str(uuid_lib.uuid4())
        object_name = f"videos/{uid}.mp4"
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            object_name,
            buf,
            length=len(buf.getbuffer()),
            content_type="video/mp4",
        )

        # Пишем запись в БД (по умолчанию rate=0)
        await create_video_feedback(VideoFeedbackCreate(file=object_name, rate=0))

        await state.clear()
        await message.answer("✅ Видео-отзыв сохранён!", reply_markup=get_actions_keyboard("video"))
    except Exception as e:
        logger.exception("Ошибка загрузки видео: %s", e)
        await state.clear()
        await message.answer("❌ Не удалось сохранить видео. Попробуйте ещё раз.", reply_markup=get_actions_keyboard("video"))

@dp.callback_query(StateFilter(FeedbackStates.waiting_for_rate), F.data.startswith("rate_"))
async def process_feedback_rate(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    try:
        rate = int(callback.data.split("_", 1)[1])
        data = await state.get_data()
        feedback_data = FeedbackCreate(text=data["text"], rate=rate)
        await create_feedback(feedback_data)
        await state.clear()

        text = "⭐ <b>Отзывы</b>\n\n✅ Отзыв успешно добавлен!\n\nВыберите действие:"
        try:
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard("text"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_actions_keyboard("text"))
    except Exception as e:
        logger.exception("Ошибка при добавлении отзыва: %s", e)
        await state.clear()
        text = "⭐ <b>Отзывы</b>\n\n❌ Ошибка при добавлении отзыва.\n\nВыберите действие:"
        try:
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard("text"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_actions_keyboard("text"))
    await callback.answer()

@dp.callback_query(F.data.startswith("delete_feedback_"))
async def delete_feedback_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return

    try:
        feedback_id = int(callback.data.split("_")[2])
        success = await delete_feedback(feedback_id)

        if success:
            text = "⭐ <b>Отзывы</b>\n\n✅ Отзыв успешно удалён!\n\nВыберите действие:"
        else:
            text = "⭐ <b>Отзывы</b>\n\n❌ Ошибка при удалении отзыва.\n\nВыберите действие:"

        try:
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard("text"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_actions_keyboard("text"))
            
    except Exception as e:
        logger.exception("Ошибка при удалении отзыва: %s", e)
        text = "⭐ <b>Отзывы</b>\n\n❌ Ошибка при удалении отзыва.\n\nВыберите действие:"
        try:
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard("text"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_actions_keyboard("text"))

    await callback.answer()

@dp.callback_query(F.data.startswith("delete_video_"))
async def delete_video_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к этому боту.")
        return
    try:
        uuid_val = callback.data.split("_", 2)[2]
        video = await get_video_feedback_by_uuid(uuid_val)
        if not video:
            text = "📹 <b>Видео-отзывы</b>\n\n❌ Видео не найдено."
        else:
            # Удаляем из MinIO, затем из БД
            try:
                minio_client.remove_object(settings.MINIO_BUCKET_NAME, video.file)
            except Exception:
                pass
            success = await delete_video_feedback(uuid_val)
            text = (
                "📹 <b>Видео-отзывы</b>\n\n✅ Видео успешно удалено!"
                if success else
                "📹 <b>Видео-отзывы</b>\n\n❌ Ошибка при удалении видео."
            )
        try:
            await callback.message.edit_text(text, reply_markup=get_actions_keyboard("video"))
        except Exception:
            await callback.message.answer(text, reply_markup=get_actions_keyboard("video"))
    except Exception as e:
        logger.exception("Ошибка при удалении видео: %s", e)
        try:
            await callback.message.edit_text("📹 <b>Видео-отзывы</b>\n\n❌ Ошибка при удалении видео.", reply_markup=get_actions_keyboard("video"))
        except Exception:
            await callback.message.answer("📹 <b>Видео-отзывы</b>\n\n❌ Ошибка при удалении видео.", reply_markup=get_actions_keyboard("video"))
    await callback.answer()

# --- Фолбэк ---
@dp.message()
async def message_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    await message.answer("Используйте /start для доступа к меню.")

# --- Start/Task ---

async def start_bot():
    try:
        logger.info("Инициализация MinIO...")
        await init_minio()
        logger.info("Запуск Telegram бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Ошибка при запуске бота: %s", e)

def start_bot_task():
    asyncio.create_task(start_bot())
