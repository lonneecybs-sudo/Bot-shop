from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID, ADMIN_PASSWORD
from keyboards import (
    get_admin_main_keyboard, get_development_keyboard,
    get_back_keyboard, get_admin_reviews_keyboard
)
from states import OrderStates
from database import (
    get_order, orders, get_stats, get_approved_reviews,
    approve_review, reject_review, reviews
)

async def admin_login_start(message: Message, state: FSMContext):
    if message.from_user.id == ADMIN_ID:
        await state.set_state(OrderStates.admin_login)
        await message.answer("🔐 <b>Введите пароль:</b>", parse_mode="HTML")
    else:
        await message.answer("⛔ Доступ запрещен!")

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

async def admin_all_orders(callback: CallbackQuery):
    if not orders:
        await callback.message.edit_text("📋 Нет заказов", reply_markup=get_admin_main_keyboard())
        return
    
    text = "📋 <b>ВСЕ ЗАКАЗЫ</b>\n\n"
    for order_id, order in sorted(orders.items(), reverse=True)[:10]:
        status = order.status
        paid = '✅' if order.paid else '❌'
        text += f"#{order_id} @{order.username} | {order.tariff.value[0]} | Опл:{paid}\n"
    
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")

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

async def admin_reviews(callback: CallbackQuery):
    pending_reviews = [r for r in reviews if not r.approved]
    
    if not pending_reviews:
        await callback.message.edit_text(
            "📋 Нет отзывов на модерации",
            reply_markup=get_admin_main_keyboard()
        )
        return
    
    for review in pending_reviews[:5]:
        text = (
            f"💬 <b>Отзыв #{review.id}</b>\n\n"
            f"От: @{review.username}\n"
            f"Оценка: {'⭐' * review.rating}\n"
            f"Текст: {review.text}\n"
            f"Дата: {review.date.strftime('%d.%m.%Y')}"
        )
        await callback.message.answer(
            text,
            reply_markup=get_admin_reviews_keyboard(review.id),
            parse_mode="HTML"
        )

async def approve_review_handler(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[2])
    if approve_review(review_id):
        await callback.message.edit_text("✅ Отзыв одобрен!")
    else:
        await callback.answer("Ошибка!", show_alert=True)

async def reject_review_handler(callback: CallbackQuery):
    review_id = int(callback.data.split("_")[2])
    reject_review(review_id)
    await callback.message.edit_text("❌ Отзыв отклонен")

def register_handlers(dp):
    dp.message.register(admin_login_start, F.text == "👑 АДМИН ПАНЕЛЬ")
    dp.message.register(check_admin_password, OrderStates.admin_login)
    dp.callback_query.register(admin_all_orders, F.data == "admin_all_orders", OrderStates.admin_in_panel)
    dp.callback_query.register(admin_stats, F.data == "admin_stats", OrderStates.admin_in_panel)
    dp.callback_query.register(admin_reviews, F.data == "admin_reviews", OrderStates.admin_in_panel)
    dp.callback_query.register(approve_review_handler, F.data.startswith("approve_review_"))
    dp.callback_query.register(reject_review_handler, F.data.startswith("reject_review_"))
