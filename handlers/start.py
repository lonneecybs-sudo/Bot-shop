from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import add_user

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    add_user(user.id, user.username, user.first_name)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="📝 Отзывы", callback_data="back_to_reviews")],
        [InlineKeyboardButton(text="🛒 Мои заказы", callback_data="my_orders")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")]
    ])
    
    await message.answer(
        f"👋 *Добро пожаловать, {user.first_name}!*\n\n"
        "Это бот-магазин. Здесь вы можете:\n"
        "• Просматривать каталог товаров\n"
        "• Оформлять заказы\n"
        "• Оставлять отзывы о товарах\n"
        "• Читать отзывы других покупателей",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню"""
    await cmd_start(callback.message)
    await callback.answer()

@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    """Информация о магазине"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "ℹ️ *О нашем магазине*\n\n"
        "Мы - команда профессионалов, работающая с 2020 года.\n"
        "• Только качественные товары\n"
        "• Быстрая доставка\n"
        "• Гарантия качества\n"
        "• Честные отзывы покупателей",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()
