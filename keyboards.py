from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup, 
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# === REPLY KEYBOARD ===
def get_reply_main_keyboard():
    """Главная клавиатура с обычными кнопками"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 ЗАКАЗАТЬ БОТА"), KeyboardButton(text="📋 МОИ ЗАКАЗЫ")],
            [KeyboardButton(text="📜 ПРАВИЛА"), KeyboardButton(text="❓ FAQ")],
            [KeyboardButton(text="💰 ТАРИФЫ"), KeyboardButton(text="💬 ОТЗЫВЫ")],
            [KeyboardButton(text="👑 АДМИН ПАНЕЛЬ")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Меню студии разработки..."
    )
    return keyboard

# === INLINE KEYBOARDS ===
def get_main_inline_keyboard():
    """Главное меню с инлайн кнопками"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 НАЧАТЬ ЗАКАЗ", callback_data="order")],
            [InlineKeyboardButton(text="📋 МОИ ЗАКАЗЫ", callback_data="my_orders")],
            [InlineKeyboardButton(text="💬 ОТЗЫВЫ", callback_data="show_reviews")],
            [
                InlineKeyboardButton(text="📜 ПРАВИЛА", callback_data="rules"),
                InlineKeyboardButton(text="❓ FAQ", callback_data="faq")
            ],
            [InlineKeyboardButton(text="💰 ТАРИФЫ", callback_data="prices")]
        ]
    )

def get_back_keyboard():
    """Клавиатура с кнопкой НАЗАД"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀ НАЗАД", callback_data="back_to_main")]
        ]
    )

def get_review_rating_keyboard():
    """Клавиатура для оценки отзыва (1-5 звезд)"""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 6):
        builder.button(
            text=f"{'⭐' * i}",
            callback_data=f"rate_{i}"
        )
    
    builder.adjust(5)
    return builder.as_markup()

def get_admin_reviews_keyboard(review_id: int):
    """Клавиатура для модерации отзывов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ ОДОБРИТЬ", callback_data=f"approve_review_{review_id}"),
                InlineKeyboardButton(text="❌ ОТКЛОНИТЬ", callback_data=f"reject_review_{review_id}")
            ]
        ]
    )

# Остальные клавиатуры (без изменений)...
def get_tariff_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ 50⭐ - Минимальный", callback_data="tariff_min")],
            [InlineKeyboardButton(text="⭐⭐ 100⭐ - Средний", callback_data="tariff_mid")],
            [InlineKeyboardButton(text="⭐⭐⭐ 300⭐ - Полный", callback_data="tariff_max")],
            [InlineKeyboardButton(text="◀ НАЗАД", callback_data="back_to_main")]
        ]
    )

def get_payment_keyboard(order_id: int, stars_amount: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⭐ ОПЛАТИТЬ {stars_amount} ЗВЕЗД", pay=True)],
            [InlineKeyboardButton(text="◀ ОТМЕНА", callback_data="back_to_main")]
        ]
    )

def get_admin_order_keyboard(order_id: int, is_free: bool = False):
    buttons = []
    if is_free:
        buttons.append([InlineKeyboardButton(text="🆓 ПРИНЯТЬ БЕСПЛАТНО", callback_data=f"accept_free_{order_id}")])
    buttons.append([InlineKeyboardButton(text="✅ ПРИНЯТЬ ЗАКАЗ", callback_data=f"accept_{order_id}")])
    buttons.append([InlineKeyboardButton(text="❌ ОТКАЗАТЬ", callback_data=f"reject_{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_development_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✉️ НАПИСАТЬ КЛИЕНТУ", callback_data=f"write_{order_id}")],
            [InlineKeyboardButton(text="✅ БОТ ГОТОВ", callback_data=f"ready_{order_id}")],
            [InlineKeyboardButton(text="📊 СТАТУС", callback_data=f"status_{order_id}")]
        ]
    )

def get_client_order_keyboard(order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 МОИ ЗАКАЗЫ", callback_data="my_orders")],
            [InlineKeyboardButton(text="⭐ ОСТАВИТЬ ОТЗЫВ", callback_data=f"leave_review_{order_id}")],
            [InlineKeyboardButton(text="◀ ГЛАВНОЕ МЕНЮ", callback_data="back_to_main")]
        ]
    )

def get_admin_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 ВСЕ ЗАКАЗЫ", callback_data="admin_all_orders")],
            [
                InlineKeyboardButton(text="⏳ В ОЖИДАНИИ", callback_data="admin_pending"),
                InlineKeyboardButton(text="🛠️ В РАЗРАБОТКЕ", callback_data="admin_development")
            ],
            [
                InlineKeyboardButton(text="✅ ЗАВЕРШЕННЫЕ", callback_data="admin_completed"),
                InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="admin_stats")
            ],
            [InlineKeyboardButton(text="💬 ОТЗЫВЫ (модерация)", callback_data="admin_reviews")],
            [InlineKeyboardButton(text="◀ ВЫЙТИ", callback_data="back_to_main")]
        ]
    )
