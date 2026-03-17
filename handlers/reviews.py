from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID, logger
from keyboards import (
    get_review_rating_keyboard, 
    get_back_keyboard,
    get_client_order_keyboard,
    get_admin_reviews_keyboard,
    get_main_inline_keyboard
)
from states import OrderStates
from database import create_review, get_approved_reviews, get_order, get_user_orders

async def show_reviews(callback: CallbackQuery):
    """Показать все одобренные отзывы"""
    try:
        approved = get_approved_reviews()
        
        if not approved:
            await callback.message.delete()
            await callback.message.answer(
                "💬 <b>ОТЗЫВОВ ПОКА НЕТ</b>\n\n"
                "Будьте первым, кто оставит отзыв после завершения заказа!",
                reply_markup=get_back_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        
        text = "💬 <b>ОТЗЫВЫ НАШИХ КЛИЕНТОВ</b>\n\n"
        
        for review in approved[-10:]:
            stars = "⭐" * review['rating']
            text += f"{stars}\n"
            text += f"<b>@{review['username']}:</b>\n"
            text += f"{review['text']}\n"
            text += f"📅 {review['date'].strftime('%d.%m.%Y')}\n"
            text += "─" * 30 + "\n\n"
        
        await callback.message.delete()
        await callback.message.answer(
            text, 
            reply_markup=get_back_keyboard(), 
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в show_reviews: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при загрузке отзывов",
            reply_markup=get_back_keyboard()
        )

async def leave_review_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания отзыва"""
    try:
        order_id = int(callback.data.split("_")[2])
        order = get_order(order_id)
        
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return
        
        if order.user_id != callback.from_user.id:
            await callback.answer("❌ Это не ваш заказ!", show_alert=True)
            return
        
        if order.status != 'completed':
            await callback.answer(
                "❌ Можно оставить отзыв только после завершения заказа!", 
                show_alert=True
            )
            return
        
        # Проверяем, не оставлял ли уже отзыв
        from database import reviews
        for review in reviews:
            if review['user_id'] == callback.from_user.id and review.get('order_id') == order_id:
                await callback.answer("❌ Вы уже оставляли отзыв для этого заказа!", show_alert=True)
                return
        
        await state.update_data(review_order_id=order_id)
        await state.set_state(OrderStates.waiting_for_review_rating)
        
        await callback.message.delete()
        await callback.message.answer(
            "⭐ <b>ОЦЕНИТЕ РАБОТУ</b>\n\n"
            "Выберите оценку от 1 до 5 звезд:",
            reply_markup=get_review_rating_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в leave_review_start: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

async def review_rating_chosen(callback: CallbackQuery, state: FSMContext):
    """Выбор оценки"""
    try:
        rating = int(callback.data.split("_")[1])
        
        if rating < 1 or rating > 5:
            await callback.answer("❌ Неверная оценка", show_alert=True)
            return
        
        await state.update_data(review_rating=rating)
        await state.set_state(OrderStates.waiting_for_review_text)
        
        await callback.message.delete()
        await callback.message.answer(
            f"📝 <b>НАПИШИТЕ ОТЗЫВ</b>\n\n"
            f"Ваша оценка: {'⭐' * rating}\n\n"
            f"Напишите несколько слов о работе разработчика:",
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в review_rating_chosen: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

async def review_text_received(message: Message, state: FSMContext):
    """Получение текста отзыва"""
    try:
        data = await state.get_data()
        
        if 'review_rating' not in data or 'review_order_id' not in data:
            await message.answer(
                "❌ Ошибка: не найдены данные отзыва. Начните заново.",
                reply_markup=get_main_inline_keyboard()
            )
            await state.clear()
            return
        
        rating = data['review_rating']
        order_id = data['review_order_id']
        
        # Создаем отзыв
        review_id = create_review(
            user_id=message.from_user.id,
            username=message.from_user.username or "Пользователь",
            rating=rating,
            text=message.text,
            order_id=order_id
        )
        
        await state.clear()
        
        await message.answer(
            f"✅ <b>СПАСИБО ЗА ОТЗЫВ!</b>\n\n"
            f"Ваш отзыв отправлен на модерацию.\n"
            f"После проверки он появится в общем списке.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        
        # Уведомление админу
        from config import bot
        await bot.send_message(
            ADMIN_ID,
            f"📝 <b>НОВЫЙ ОТЗЫВ НА МОДЕРАЦИИ</b>\n\n"
            f"От: @{message.from_user.username or 'Пользователь'}\n"
            f"Оценка: {'⭐' * rating}\n"
            f"Текст: {message.text}\n\n"
            f"ID отзыва: {review_id}",
            reply_markup=get_admin_reviews_keyboard(review_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка в review_text_received: {e}")
        await message.answer(
            "❌ Произошла ошибка при сохранении отзыва",
            reply_markup=get_back_keyboard()
        )
        await state.clear()

async def approve_review_handler(callback: CallbackQuery):
    """Одобрить отзыв"""
    review_id = int(callback.data.split("_")[2])
    from database import approve_review
    if approve_review(review_id):
        await callback.message.edit_text("✅ Отзыв одобрен!")
    else:
        await callback.answer("❌ Ошибка!", show_alert=True)

async def reject_review_handler(callback: CallbackQuery):
    """Отклонить отзыв"""
    review_id = int(callback.data.split("_")[2])
    from database import reject_review
    reject_review(review_id)
    await callback.message.edit_text("❌ Отзыв отклонен")

def register_handlers(dp):
    """Регистрация обработчиков отзывов"""
    dp.callback_query.register(show_reviews, F.data == "show_reviews")
    dp.callback_query.register(leave_review_start, F.data.startswith("leave_review_"))
    dp.callback_query.register(review_rating_chosen, F.data.startswith("rate_"), OrderStates.waiting_for_review_rating)
    dp.message.register(review_text_received, OrderStates.waiting_for_review_text)
    dp.callback_query.register(approve_review_handler, F.data.startswith("approve_review_"))
    dp.callback_query.register(reject_review_handler, F.data.startswith("reject_review_"))
