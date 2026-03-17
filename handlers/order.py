from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import Tariff, ADMIN_ID, logger
from keyboards import (
    get_tariff_keyboard, 
    get_client_order_keyboard,
    get_admin_order_keyboard, 
    get_back_keyboard
)
from states import OrderStates
from database import create_order, get_order, get_user_orders
import database

router = Router()

@router.callback_query(F.data == "order")
async def order_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "📦 <b>ВЫБЕРИТЕ ТАРИФ</b>\n\n"
        "┌─────────────────────────┐\n"
        "│ ⭐ МИНИМАЛЬНЫЙ • 50⭐    │\n"
        "│ Базовые команды         │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐ СРЕДНИЙ • 100⭐     │\n"
        "│ Команды + инлайн кнопки │\n"
        "├─────────────────────────┤\n"
        "│ ⭐⭐⭐ ПОЛНЫЙ • 300⭐     │\n"
        "│ Любые функции, кастом   │\n"
        "└─────────────────────────┘\n\n"
        "<i>Выберите подходящий тариф:</i>",
        reply_markup=get_tariff_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("tariff_"))
async def tariff_chosen(callback: CallbackQuery, state: FSMContext):
    tariff_map = {
        "tariff_min": Tariff.MIN,
        "tariff_mid": Tariff.MID,
        "tariff_max": Tariff.MAX
    }
    
    tariff = tariff_map[callback.data]
    await state.update_data(tariff=tariff)
    await state.set_state(OrderStates.entering_description)
    
    await callback.message.delete()
    await callback.message.answer(
        f"📝 <b>ОПИШИТЕ ЗАДАЧУ</b>\n\n"
        f"Выбран тариф: {tariff.value[0]} ({tariff.value[1]}⭐)\n\n"
        f"<b>Пример:</b>\n"
        f"• Бот для магазина\n"
        f"• Админка для товаров\n"
        f"• Корзина и оплата\n\n"
        f"<i>Отправьте описание одним сообщением:</i>",
        parse_mode="HTML"
    )

@router.message(OrderStates.entering_description)
async def description_received(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    tariff = data['tariff']
    
    order_id = create_order(
        user_id=message.from_user.id,
        username=message.from_user.username or "нет username",
        tariff=tariff,
        description=message.text
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>ЗАКАЗ №{order_id} ОФОРМЛЕН!</b>\n\n"
        f"Тариф: {tariff.value[0]}\n"
        f"Сумма: {tariff.value[1]}⭐\n\n"
        f"⏳ Ожидайте подтверждения от разработчика",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    # Уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"🔔 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
        f"От: @{message.from_user.username or 'нет username'}\n"
        f"Тариф: {tariff.value[0]}\n"
        f"Сумма: {tariff.value[1]}⭐\n\n"
        f"<b>Описание:</b>\n{message.text}",
        reply_markup=get_admin_order_keyboard(order_id, is_free=True),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    user_orders = get_user_orders(callback.from_user.id)
    
    if not user_orders:
        await callback.message.delete()
        await callback.message.answer(
            "📋 <b>У вас пока нет заказов</b>\n\n"
            "Нажмите «Заказать бота», чтобы оформить заказ.",
            reply_markup=get_back_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = "📋 <b>ВАШИ ЗАКАЗЫ</b>\n\n"
    for order in sorted(user_orders, key=lambda x: x['created_at'], reverse=True)[:5]:
        status_emoji = {
            'pending': '⏳',
            'waiting_payment': '💰',
            'development': '🛠️',
            'completed': '✅'
        }.get(order['status'], '⏳')
        
        status_text = {
            'pending': 'Ожидает',
            'waiting_payment': 'Ожидает оплаты',
            'development': 'В разработке',
            'completed': 'Готов'
        }.get(order['status'], 'Неизвестно')
        
        text += f"{status_emoji} <b>Заказ №{order['id']}</b>\n"
        text += f"└ {order['tariff'].value[0]} | {status_text}\n"
        text += f"└ {order['created_at'].strftime('%d.%m.%Y')}\n\n"
    
    text += "<i>Статусы обновляются автоматически</i>"
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
