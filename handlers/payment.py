from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from keyboards import (
    get_development_keyboard,
    get_client_order_keyboard,
    get_back_keyboard
)
from database import get_order, mark_order_paid

class PaymentStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_token = State()

router = Router()

@router.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: CallbackQuery, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    parts = callback.data.split("_")
    if len(parts) == 2:
        order_id = int(parts[1])
        is_free = False
    else:
        order_id = int(parts[2])
        is_free = True
    
    order = get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    if is_free:
        mark_order_paid(order_id)
        order['status'] = 'development'
        
        await bot.send_message(
            order['user_id'],
            f"🆓 <b>ЗАКАЗ №{order_id} ПРИНЯТ БЕСПЛАТНО!</b>",
            reply_markup=get_client_order_keyboard(order_id),
            parse_mode="HTML"
        )
        await callback.message.edit_text(f"✅ Заказ #{order_id} принят БЕСПЛАТНО!")
        
        await bot.send_message(
            ADMIN_ID,
            f"🆓 Бесплатный заказ #{order_id} принят.\nКлиент: @{order['username']}",
            reply_markup=get_development_keyboard(order_id),
            parse_mode="HTML"
        )
    else:
        order['status'] = 'waiting_payment'
        prices = [LabeledPrice(label=f"Заказ #{order_id}", amount=order['tariff'].value[1])]
        
        await bot.send_invoice(
            chat_id=order['user_id'],
            title=f"Оплата заказа #{order_id}",
            description=f"Тариф: {order['tariff'].value[0]}",
            payload=f"order_{order_id}",
            provider_token="",
            currency="XTR",
            prices=prices
        )
        await callback.message.edit_text(f"✅ Заказ #{order_id} принят, счет отправлен")

@router.callback_query(F.data.startswith("write_"))
async def write_to_client(callback: CallbackQuery, state: FSMContext, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    await state.update_data(write_order_id=order_id)
    await state.set_state(PaymentStates.waiting_for_message)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✉️ Введите сообщение для @{order['username']}:",
        parse_mode="HTML"
    )

@router.message(PaymentStates.waiting_for_message)
async def send_message_to_client(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    order_id = data.get('write_order_id')
    order = get_order(order_id)
    
    await bot.send_message(
        order['user_id'],
        f"📩 <b>Сообщение от разработчика</b>\n\n{message.text}",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    await state.clear()
    await message.answer("✅ Отправлено!", reply_markup=get_development_keyboard(order_id))

@router.callback_query(F.data.startswith("ready_"))
async def bot_ready(callback: CallbackQuery, state: FSMContext, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    await state.update_data(ready_order_id=order_id)
    await state.set_state(PaymentStates.waiting_for_token)
    
    await callback.message.delete()
    await callback.message.answer("✅ Введите API токен готового бота:")

@router.message(PaymentStates.waiting_for_token)
async def send_token_to_client(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    order_id = data.get('ready_order_id')
    order = get_order(order_id)
    
    token = message.text
    order['status'] = 'completed'
    order['token'] = token
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    await bot.send_message(
        order['user_id'],
        f"🎉 <b>ТВОЙ БОТ ГОТОВ!</b>\n\n<code>{token}</code>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="✅ ПОДТВЕРДИТЬ", callback_data=f"confirm_{order_id}")]]
        ),
        parse_mode="HTML"
    )
    
    await state.clear()
    await message.answer("✅ Токен отправлен!", reply_markup=get_development_keyboard(order_id))

@router.callback_query(F.data.startswith("status_"))
async def check_status(callback: CallbackQuery, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    status_text = {
        'pending': '⏳ Ожидает',
        'waiting_payment': '💰 Ожидает оплаты',
        'development': '🛠️ В разработке',
        'completed': '✅ Готов'
    }.get(order['status'], 'Неизвестно')
    
    await callback.message.edit_text(
        f"📊 Статус заказа #{order_id}: {status_text}",
        reply_markup=get_development_keyboard(order_id)
    )

@router.callback_query(F.data.startswith("confirm_"))
async def confirm_receipt(callback: CallbackQuery, bot):
    order_id = int(callback.data.split("_")[1])
    await callback.message.edit_text("✅ Заказ завершен!", reply_markup=get_back_keyboard())
    await bot.send_message(ADMIN_ID, f"✅ Клиент подтвердил получение заказа #{order_id}")

@router.callback_query(F.data.startswith("reject_"))
async def reject_order(callback: CallbackQuery, bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    if order:
        await bot.send_message(
            order['user_id'],
            f"❌ <b>ЗАКАЗ №{order_id} ОТКЛОНЕН</b>",
            parse_mode="HTML"
        )
        
        from database import orders
        if order_id in orders:
            del orders[order_id]
    
    await callback.message.edit_text(f"❌ Заказ #{order_id} отклонен")

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, bot):
    payload = message.successful_payment.invoice_payload
    order_id = int(payload.split("_")[1])
    
    mark_order_paid(order_id)
    order = get_order(order_id)
    
    await message.answer(
        f"✅ Оплата подтверждена! Заказ #{order_id} в разработке.",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    await bot.send_message(
        ADMIN_ID,
        f"💰 Заказ #{order_id} оплачен!\nКлиент: @{order['username']}",
        reply_markup=get_development_keyboard(order_id),
        parse_mode="HTML"
    )
