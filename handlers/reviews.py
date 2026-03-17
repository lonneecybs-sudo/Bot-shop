from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID
from keyboards import (
    get_review_rating_keyboard,
    get_back_keyboard,
    get_client_order_keyboard,
    get_admin_reviews_keyboard
)
from states import OrderStates
from database import create_review, get_approved_reviews, get_order

router = Router()

@router.callback_query(F.data == "show_reviews")
async def show_reviews(callback: CallbackQuery):
    approved = get_approved_reviews()
    
    if not approved:
        await callback.message.delete()
        await callback.message.answer(
            "💬 <b>ОТЗЫВОВ ПОКА НЕТ</b>",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "💬 <b>ОТЗЫВЫ НАШИХ КЛИЕНТОВ</b>\n\n"
    for review in approved[-10:]:
        stars = "⭐" * review['rating']
        text += f"{stars}\n"
        text += f"<b>@{review['username']}:</b>\n"
        text += f"{review['text']}\n"
        text += f"📅 {review['date'].strftime('%d.%m.%Y')}\n\n"
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("leave_review_"))
async def leave_review_start(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    order = get_order(order_id)
    
    if not order or order['user_id'] != callback.from_user.id:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    if order['status'] != 'completed':
        await callback.answer("❌ Можно оставить отзыв только после завершения заказа!", show_alert=True)
        return
    
    await state.update_data(review_order_id=order_id)
    await state.set_state(OrderStates.waiting_for_review_rating)
    
    await callback.message.delete()
    await callback.message.answer(
        "⭐ <b>ОЦЕНИТЕ РАБОТУ</b>\n\nВыберите оценку:",
        reply_markup=get_review_rating_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("rate_"), OrderStates.waiting_for_review_rating)
async def review_rating_chosen(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(review_rating=rating)
    await state.set_state(OrderStates.waiting_for_review_text)
    
    await callback.message.delete()
    await callback.message.answer(
        f"📝 <b>НАПИШИТЕ ОТЗЫВ</b>\n\nОценка: {'⭐' * rating}\n\nНапишите текст отзыва:",
        parse_mode="HTML"
    )

@router.message(OrderStates.waiting_for_review_text)
async def review_text_received(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    rating = data['review_rating']
    order_id = data['review_order_id']
    
    review_id = create_review(
        user_id=message.from_user.id,
        username=message.from_user.username or "Пользователь",
        rating=rating,
        text=message.text,
        order_id=order_id
    )
    
    await state.clear()
    
    await message.answer(
