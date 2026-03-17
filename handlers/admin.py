from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID, ADMIN_PASSWORD
from keyboards import (
    get_admin_main_keyboard,
    get_back_keyboard,
    get_development_keyboard,
    get_admin_reviews_keyboard
)
from states import OrderStates
from database import orders, get_stats, get_pending_reviews, approve_review, reject_review

router = Router()

@router.message(OrderStates.admin_login)
async def check_admin_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        await state.set_state(OrderStates.admin_in_panel)
        await message.answer(
            "👑 <b>АДМИН ПАНЕЛЬ</b>\n\nВыберите раздел:",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Неверный пароль!")
        await state.clear()

@router.callback_query(F.data == "admin_all_orders", OrderStates.admin_in_panel)
async def admin_all_orders(callback: CallbackQuery):
    if not orders:
        await callback.message.edit_text(
            "📋 Нет заказов",
            reply_markup=get_admin_main_keyboard()
        )
        return
    
    text = "📋 <b>ВСЕ ЗАКАЗЫ</b>\n\n"
    for order_id, order in sorted(orders.items(), reverse=True)[:10]:
        paid = '✅' if order.get('paid', False) else '❌'
        text += f"#{order_id} @{order['username']} | {order['tariff'].value[0]} | Опл:{paid}\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_stats", OrderStates.admin_in_panel)
async def admin_stats(callback: CallbackQuery):
    stats = get_stats()
    text = (
        "📊 <b>СТАТИСТИКА</b>\n\n"
        f"📋 Всего заказов: {stats['total_orders']}\n"
        f"✅ Завершено: {stats['completed']}\n"
        f"💰 Оплачено: {stats['paid']}\n"
        f"⭐ Заработано: {stats['total_stars']}\n"
        f"💬 Отзывов: {stats['reviews_count']}"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "admin_reviews", OrderStates.admin_in_panel)
async def admin_reviews(callback: CallbackQuery):
    pending = get_pending_reviews()
    
    if not pending:
        await callback.message.edit_text(
            "📋 Нет отзывов на модерации",
            reply_markup=get_admin_main_keyboard()
        )
        return
    
    await callback.message.delete()
    for review in pending[:5]:
        text = (
            f"💬 <b>Отзыв #{review['id']}</b>\n\n"
            f"От: @{review['username']}\n"
            f"Оценка: {'⭐' * review['rating']}\n"
            f"Текст: {review['text']}\n"
            f"Дата: {review['date'].strftime('%d.%m.%Y')}"
        )
        await callback.message.answer(
            text,
            reply_markup=get_admin_reviews_keyboard(review['id']),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("approve_review_"))
async def approve_review_handler(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[2])
    if approve_review(review_id):
        await callback.message.edit_text("✅ Отзыв одобрен!")
    else:
        await callback.answer("❌ Ошибка!", show_alert=True)

@router.callback_query(F.data.startswith("reject_review_"))
async def reject_review_handler(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[2])
    reject_review(review_id)
    await callback.message.edit_text("❌ Отзыв отклонен")
