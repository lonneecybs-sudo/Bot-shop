from aiogram import F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID, logger
from keyboards import (
    get_development_keyboard, 
    get_client_order_keyboard,
    get_back_keyboard
)
from database import get_order, mark_order_paid, update_order_status

# Состояния для ожидания ввода
class PaymentStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_token = State()

async def accept_order(callback: CallbackQuery, bot):
    """Админ принимает заказ"""
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
        order.status = 'development'
        
        await bot.send_message(
            order.user_id,
            f"🆓 <b>ЗАКАЗ №{order_id} ПРИНЯТ БЕСПЛАТНО!</b>\n\n"
            f"Разработчик начал работу над вашим ботом!",
            reply_markup=get_client_order_keyboard(order_id),
            parse_mode="HTML"
        )
        
        await callback.message.edit_text(f"✅ Заказ #{order_id} принят БЕСПЛАТНО!")
        
        await bot.send_message(
            ADMIN_ID,
            f"🆓 Бесплатный заказ #{order_id} принят.\n"
            f"Клиент: @{order.username}\n\n"
            f"Можно начинать разработку!",
            reply_markup=get_development_keyboard(order_id),
            parse_mode="HTML"
        )
    else:
        order.status = 'waiting_payment'
        
        prices = [LabeledPrice(
            label=f"Заказ #{order_id} - {order.tariff.value[0]}", 
            amount=order.tariff.value[1]
        )]
        
        await bot.send_invoice(
            chat_id=order.user_id,
            title=f"Оплата заказа #{order_id}",
            description=f"Тариф: {order.tariff.value[0]}\nСумма: {order.tariff.value[1]}⭐",
            payload=f"order_{order_id}",
            provider_token="",
            currency="XTR",
            prices=prices,
            reply_markup=None
        )
        
        await callback.message.edit_text(f"✅ Заказ #{order_id} принят, счет отправлен клиенту")
        
        await bot.send_message(
            ADMIN_ID,
            f"💰 Заказ #{order_id} принят.\n"
            f"Клиент: @{order.username}\n"
            f"Сумма: {order.tariff.value[1]}⭐\n\n"
            f"Ожидаем оплату...",
            parse_mode="HTML"
        )

# ========== ИСПРАВЛЯЕМ КНОПКУ "НАПИСАТЬ КЛИЕНТУ" ==========
async def write_to_client(callback: CallbackQuery, state: FSMContext, bot):
    """Написать клиенту"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    await state.update_data(write_order_id=order_id)
    await state.set_state(PaymentStates.waiting_for_message)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✉️ <b>НАПИСАТЬ КЛИЕНТУ</b>\n\n"
        f"Заказ №{order_id}\n"
        f"Клиент: @{order.username}\n\n"
        f"Введите сообщение для клиента:",
        parse_mode="HTML"
    )

async def send_message_to_client(message: Message, state: FSMContext, bot):
    """Отправка сообщения клиенту"""
    data = await state.get_data()
    order_id = data.get('write_order_id')
    
    if not order_id:
        await message.answer("❌ Ошибка: не найден ID заказа")
        await state.clear()
        return
    
    order = get_order(order_id)
    if not order:
        await message.answer("❌ Ошибка: заказ не найден")
        await state.clear()
        return
    
    await bot.send_message(
        order.user_id,
        f"📩 <b>СООБЩЕНИЕ ОТ РАЗРАБОТЧИКА</b>\n\n"
        f"По заказу №{order_id}\n\n"
        f"{message.text}",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    await state.clear()
    await message.answer(
        f"✅ Сообщение отправлено клиенту @{order.username}",
        reply_markup=get_development_keyboard(order_id)
    )

# ========== ИСПРАВЛЯЕМ КНОПКУ "БОТ ГОТОВ" ==========
async def bot_ready(callback: CallbackQuery, state: FSMContext, bot):
    """Бот готов - запрос токена"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    await state.update_data(ready_order_id=order_id)
    await state.set_state(PaymentStates.waiting_for_token)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>БОТ ГОТОВ!</b>\n\n"
        f"Заказ №{order_id}\n"
        f"Клиент: @{order.username}\n\n"
        f"Введите API токен готового бота:",
        parse_mode="HTML"
    )

async def send_token_to_client(message: Message, state: FSMContext, bot):
    """Отправка токена клиенту"""
    data = await state.get_data()
    order_id = data.get('ready_order_id')
    
    if not order_id:
        await message.answer("❌ Ошибка: не найден ID заказа")
        await state.clear()
        return
    
    order = get_order(order_id)
    if not order:
        await message.answer("❌ Ошибка: заказ не найден")
        await state.clear()
        return
    
    token = message.text
    order.status = 'completed'
    order.token = token
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    await bot.send_message(
        order.user_id,
        f"🎉 <b>ТВОЙ БОТ ГОТОВ!</b>\n\n"
        f"<b>🤖 API Токен:</b>\n"
        f"<code>{token}</code>\n\n"
        f"<b>📋 Инструкция:</b>\n"
        f"1. Перейди в @BotFather\n"
        f"2. Отправь команду /mybots\n"
        f"3. Выбери бота и нажми 'API Token'\n"
        f"4. Вставь этот токен\n\n"
        f"┌─────────────────────────┐\n"
        f"│  ✅ ПОДТВЕРДИТЬ ПОЛУЧЕНИЕ│\n"
        f"└─────────────────────────┘",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ ПОДТВЕРДИТЬ ПОЛУЧЕНИЕ", callback_data=f"confirm_{order_id}")]
            ]
        ),
        parse_mode="HTML"
    )
    
    await state.clear()
    await message.answer(
        f"✅ Токен отправлен клиенту @{order.username}",
        reply_markup=get_development_keyboard(order_id)
    )

# ========== ИСПРАВЛЯЕМ КНОПКУ "СТАТУС" ==========
async def check_status(callback: CallbackQuery, bot):
    """Проверка статуса заказа"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    status_text = {
        'pending': '⏳ Ожидает подтверждения',
        'waiting_payment': '💰 Ожидает оплаты',
        'development': '🛠️ В разработке',
        'completed': '✅ Завершен'
    }.get(order.status, 'Неизвестно')
    
    await callback.message.edit_text(
        f"📊 <b>СТАТУС ЗАКАЗА #{order_id}</b>\n\n"
        f"┌─────────────────────────┐\n"
        f"│ Клиент: @{order.username}\n"
        f"│ Тариф: {order.tariff.value[0]}\n"
        f"│ Статус: {status_text}\n"
        f"│ Оплачен: {'✅' if order.paid else '❌'}\n"
        f"│ Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"└─────────────────────────┘\n\n"
        f"<b>📝 Описание:</b>\n{order.description}",
        reply_markup=get_development_keyboard(order_id),
        parse_mode="HTML"
    )

async def confirm_receipt(callback: CallbackQuery, bot):
    """Подтверждение получения бота клиентом"""
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"✅ <b>ЗАКАЗ №{order_id} ЗАВЕРШЕН!</b>\n\n"
        f"Спасибо за заказ! Обращайтесь еще!",
        reply_markup=get_back_keyboard(),
        parse_mode="HTML"
    )
    
    await bot.send_message(
        ADMIN_ID,
        f"✅ <b>КЛИЕНТ ПОДТВЕРДИЛ ПОЛУЧЕНИЕ</b>\n\n"
        f"Заказ №{order_id}\n"
        f"Клиент: @{order.username}\n\n"
        f"Заказ успешно завершен!",
        parse_mode="HTML"
    )

async def reject_order(callback: CallbackQuery, bot):
    """Админ отклоняет заказ"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    if order:
        await bot.send_message(
            order.user_id,
            f"❌ <b>ЗАКАЗ №{order_id} ОТКЛОНЕН</b>\n\n"
            f"К сожалению, разработчик не может принять этот заказ.\n"
            f"Попробуйте оформить заказ с другим описанием.",
            parse_mode="HTML"
        )
        
        from database import orders
        if order_id in orders:
            del orders[order_id]
    
    await callback.message.edit_text(f"❌ Заказ #{order_id} отклонен")

async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, bot):
    """Подтверждение pre-checkout запроса"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    logger.info(f"✅ Pre-checkout подтвержден: {pre_checkout_query.invoice_payload}")

async def successful_payment_handler(message: Message, bot):
    """Обработчик успешной оплаты"""
    payload = message.successful_payment.invoice_payload
    order_id = int(payload.split("_")[1])
    total_amount = message.successful_payment.total_amount
    
    mark_order_paid(order_id)
    order = get_order(order_id)
    
    await message.answer(
        f"✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\n"
        f"┌─────────────────────────┐\n"
        f"│ Заказ №{order_id}         │\n"
        f"│ Сумма: {total_amount}⭐   │\n"
        f"│ Статус: В разработке 🛠️ │\n"
        f"└─────────────────────────┘\n\n"
        f"Разработчик уже начал работу над вашим ботом!",
        reply_markup=get_client_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    await bot.send_message(
        ADMIN_ID,
        f"💰 <b>ЗАКАЗ #{order_id} ОПЛАЧЕН!</b>\n\n"
        f"┌─────────────────────────┐\n"
        f"│ Клиент: @{order.username}\n"
        f"│ Сумма: {total_amount}⭐   │\n"
        f"│ Тариф: {order.tariff.value[0]}\n"
        f"└─────────────────────────┘\n\n"
        f"Можете начинать разработку!\n\n"
        f"<b>Описание заказа:</b>\n{order.description}",
        reply_markup=get_development_keyboard(order_id),
        parse_mode="HTML"
    )

async def test_payment(callback: CallbackQuery, bot):
    """Тестовая оплата"""
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="🧪 ТЕСТОВЫЙ ПЛАТЕЖ",
        description="Проверка работы оплаты звездами",
        payload="test_payment",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Тест", amount=1)]
    )

def register_handlers(dp):
    """Регистрация всех обработчиков"""
    dp.callback_query.register(accept_order, F.data.startswith("accept_"))
    dp.callback_query.register(reject_order, F.data.startswith("reject_"))
    dp.callback_query.register(write_to_client, F.data.startswith("write_"))
    dp.callback_query.register(bot_ready, F.data.startswith("ready_"))
    dp.callback_query.register(check_status, F.data.startswith("status_"))
    dp.callback_query.register(confirm_receipt, F.data.startswith("confirm_"))
    dp.callback_query.register(test_payment, F.data == "test_payment")
    dp.message.register(send_message_to_client, PaymentStates.waiting_for_message)
    dp.message.register(send_token_to_client, PaymentStates.waiting_for_token)
    dp.pre_checkout_query.register(pre_checkout_handler)
    dp.message.register(successful_payment_handler, F.successful_payment)
