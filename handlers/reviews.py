from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import (
    create_review, get_approved_reviews, get_pending_reviews,
    get_user_orders, get_order, moderate_review, get_user_reviews,
    get_review_stats, get_product
)
import logging

router = Router()

# Состояния для FSM
class ReviewStates(StatesGroup):
    waiting_for_order_choice = State()
    waiting_for_rating = State()
    waiting_for_comment = State()
    waiting_for_moderation = State()

# ========== ПОЛЬЗОВАТЕЛЬСКИЕ ФУНКЦИИ ==========

@router.message(Command("reviews"))
async def cmd_reviews(message: Message):
    """Показать меню отзывов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
        [InlineKeyboardButton(text="⭐ Мои отзывы", callback_data="my_reviews")],
        [InlineKeyboardButton(text="📊 Все отзывы", callback_data="all_reviews")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await message.answer(
        "📝 *Управление отзывами*\n\n"
        "Вы можете оставить отзыв о товаре, посмотреть свои отзывы или почитать отзывы других покупателей.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "leave_review")
async def process_leave_review(callback: CallbackQuery, state: FSMContext):
    """Начало процесса оставления отзыва"""
    user_id = callback.from_user.id
    
    # Получаем завершенные заказы пользователя (без отзывов)
    orders = get_user_orders(user_id)
    
    # Фильтруем заказы со статусом 'completed' или 'delivered'
    eligible_orders = []
    user_reviews = get_user_reviews(user_id)
    reviewed_order_ids = [r['order_id'] for r in user_reviews]
    
    for order in orders:
        if order['status'] in ['completed', 'delivered'] and order['id'] not in reviewed_order_ids:
            eligible_orders.append(order)
    
    if not eligible_orders:
        await callback.message.edit_text(
            "❌ У вас нет завершенных заказов, на которые можно оставить отзыв.\n\n"
            "Сделайте заказ и дождитесь его выполнения!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛍 В каталог", callback_data="catalog")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
            ])
        )
        await callback.answer()
        return
    
    # Создаем клавиатуру с заказами
    keyboard = []
    for order in eligible_orders:
        keyboard.append([InlineKeyboardButton(
            text=f"🛒 Заказ #{order['id']} - {order['product_name']}",
            callback_data=f"review_order_{order['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")])
    
    await callback.message.edit_text(
        "📦 *Выберите заказ для отзыва:*\n\n"
        "Вы можете оставить отзыв только на выполненные заказы.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("review_order_"))
async def process_order_for_review(callback: CallbackQuery, state: FSMContext):
    """Выбор заказа для отзыва"""
    order_id = int(callback.data.split("_")[2])
    order = get_order(order_id)
    
    if not order:
        await callback.message.edit_text("❌ Заказ не найден.")
        await callback.answer()
        return
    
    await state.update_data(order_id=order_id, product_id=order['product_id'])
    
    # Клавиатура для выбора рейтинга
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐" * i, callback_data=f"rating_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="leave_review")]
    ])
    
    await callback.message.edit_text(
        f"⭐ *Оцените товар:*\n\n"
        f"*Товар:* {order['product_name']}\n"
        f"*Заказ:* #{order_id}\n\n"
        f"Пожалуйста, оцените товар от 1 до 5 звёзд:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("rating_"))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    """Выбор рейтинга"""
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    
    await callback.message.edit_text(
        f"✍️ *Напишите отзыв*\n\n"
        f"Вы поставили оценку: {'⭐' * rating}\n\n"
        f"Напишите текст вашего отзыва (можно отправить одним сообщением):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Пропустить комментарий", callback_data="skip_comment")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="leave_review")]
        ]),
        parse_mode="Markdown"
    )
    await state.set_state(ReviewStates.waiting_for_comment)
    await callback.answer()

@router.callback_query(F.data == "skip_comment")
async def skip_comment(callback: CallbackQuery, state: FSMContext):
    """Пропуск комментария"""
    await save_review(callback.message, state, comment=None)
    await callback.answer()

@router.message(ReviewStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    """Получение комментария"""
    comment = message.text
    await save_review(message, state, comment)

async def save_review(message: Message, state: FSMContext, comment: str = None):
    """Сохранение отзыва"""
    data = await state.get_data()
    user_id = message.from_user.id
    order_id = data.get('order_id')
    product_id = data.get('product_id')
    rating = data.get('rating')
    
    try:
        review_id = create_review(user_id, order_id, product_id, rating, comment)
        
        if review_id:
            await message.answer(
                "✅ *Спасибо за ваш отзыв!*\n\n"
                "Он отправлен на модерацию и будет опубликован после проверки.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Оставить ещё отзыв", callback_data="leave_review")],
                    [InlineKeyboardButton(text="🔙 В меню отзывов", callback_data="back_to_reviews")]
                ])
            )
        else:
            await message.answer(
                "❌ Не удалось сохранить отзыв. Возможно, вы уже оставляли отзыв на этот заказ.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
                ])
            )
    except Exception as e:
        logging.error(f"Error saving review: {e}")
        await message.answer("❌ Произошла ошибка при сохранении отзыва.")
    
    await state.clear()

@router.callback_query(F.data == "my_reviews")
async def show_my_reviews(callback: CallbackQuery):
    """Показать отзывы пользователя"""
    user_id = callback.from_user.id
    reviews = get_user_reviews(user_id)
    
    if not reviews:
        await callback.message.edit_text(
            "📭 У вас пока нет отзывов.\n\n"
            "Сделайте заказ и оставьте отзыв о товаре!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
            ])
        )
        await callback.answer()
        return
    
    text = "📝 *Мои отзывы:*\n\n"
    for review in reviews[:5]:  # Показываем последние 5
        status_emoji = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }.get(review['status'], '📝')
        
        text += f"{status_emoji} *{review['product_name']}*\n"
        text += f"Оценка: {'⭐' * review['rating']}\n"
        if review['comment']:
            text += f"Комментарий: {review['comment'][:50]}...\n" if len(review['comment']) > 50 else f"Комментарий: {review['comment']}\n"
        text += f"Статус: {review['status']}\n"
        text += f"Дата: {review['created_at'][:10]}\n\n"
    
    if len(reviews) > 5:
        text += f"*...и ещё {len(reviews) - 5} отзывов*"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data == "all_reviews")
async def show_all_reviews(callback: CallbackQuery):
    """Показать все одобренные отзывы"""
    reviews = get_approved_reviews()
    
    if not reviews:
        await callback.message.edit_text(
            "📭 Пока нет ни одного отзыва.\n\n"
            "Будьте первым, кто оставит отзыв!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
            ])
        )
        await callback.answer()
        return
    
    # Получаем общую статистику
    stats = get_review_stats()
    
    text = "⭐ *Все отзывы покупателей*\n\n"
    if stats and stats['total_reviews']:
        text += f"*Всего отзывов:* {stats['total_reviews']}\n"
        text += f"*Средняя оценка:* {stats['avg_rating']:.1f}/5.0\n\n"
    
    for review in reviews[:10]:  # Показываем последние 10
        user_name = review['first_name'] or review['username'] or f"User_{review['user_id']}"
        text += f"*{user_name}* о товаре *{review['product_name']}*\n"
        text += f"{'⭐' * review['rating']}\n"
        if review['comment']:
            text += f"_{review['comment']}_\n"
        text += f"📅 {review['created_at'][:10]}\n\n"
    
    if len(reviews) > 10:
        text += f"*...и ещё {len(reviews) - 10} отзывов*"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_review")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_reviews")]
        ])
    )
    await callback.answer()

# ========== АДМИНСКИЕ ФУНКЦИИ ==========

@router.message(Command("admin_reviews"))
async def cmd_admin_reviews(message: Message):
    """Админ-панель для модерации отзывов"""
    # Проверка на админа (можно расширить)
    if message.from_user.id not in [123456789]:  # Замените на реальные ID админов
        await message.answer("⛔ У вас нет прав администратора.")
        return
    
    await show_pending_reviews(message)

async def show_pending_reviews(message: Message):
    """Показать отзывы на модерации"""
    pending = get_pending_reviews()
    
    if not pending:
        await message.answer(
            "✅ Нет отзывов, ожидающих модерации.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh_pending")]
            ])
        )
        return
    
    text = f"⏳ *Отзывы на модерации:* {len(pending)}\n\n"
    
    for review in pending[:5]:
        user_name = review['first_name'] or review['username'] or f"User_{review['user_id']}"
        text += f"*ID:* {review['id']}\n"
        text += f"*Пользователь:* {user_name}\n"
        text += f"*Товар:* {review['product_name']}\n"
        text += f"*Оценка:* {'⭐' * review['rating']}\n"
        if review['comment']:
            text += f"*Комментарий:* {review['comment']}\n"
        text += f"*Дата:* {review['created_at']}\n\n"
    
    if len(pending) > 5:
        text += f"*...и ещё {len(pending) - 5} отзывов*"
    
    keyboard = []
    for review in pending[:5]:
        keyboard.append([
            InlineKeyboardButton(text=f"✅ Одобрить #{review['id']}", callback_data=f"admin_approve_{review['id']}"),
            InlineKeyboardButton(text=f"❌ Отклонить #{review['id']}", callback_data=f"admin_reject_{review['id']}")
        ])
    keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh_pending")])
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_review(callback: CallbackQuery):
    """Одобрение отзыва"""
    review_id = int(callback.data.split("_")[2])
    moderate_review(review_id, 'approved', callback.from_user.id)
    
    await callback.answer("✅ Отзыв одобрен!")
    await callback.message.edit_text(f"✅ Отзыв #{review_id} одобрен и опубликован.")
    
    # Показываем следующий отзыв
    await show_pending_reviews(callback.message)

@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_review(callback: CallbackQuery):
    """Отклонение отзыва"""
    review_id = int(callback.data.split("_")[2])
    moderate_review(review_id, 'rejected', callback.from_user.id)
    
    await callback.answer("❌ Отзыв отклонен!")
    await callback.message.edit_text(f"❌ Отзыв #{review_id} отклонен.")
    
    # Показываем следующий отзыв
    await show_pending_reviews(callback.message)

@router.callback_query(F.data == "admin_refresh_pending")
async def admin_refresh_pending(callback: CallbackQuery):
    """Обновление списка ожидающих отзывов"""
    await show_pending_reviews(callback.message)
    await callback.answer()

# ========== НАВИГАЦИЯ ==========

@router.callback_query(F.data == "back_to_reviews")
async def back_to_reviews(callback: CallbackQuery, state: FSMContext = None):
    """Возврат в меню отзывов"""
    if state:
        await state.clear()
    await cmd_reviews(callback.message)
    await callback.answer()
