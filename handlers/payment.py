from aiogram import F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from keyboards import get_development_keyboard, get_client_order_keyboard
from database import get_order, mark_order_paid, update_order_status

async def accept_order(callback: CallbackQuery, bot):
    """Админ принимает заказ"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    parts = callback.data.split("_")
    if len(parts) == 2:  # accept_123
        order_id = int(parts[1])
        is_free = False
    else:  # accept_free_123
        order_id = int(parts[2])
        is_free = True
    
    order = get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден!", show_alert=True)
        return
    
    if is_free:
        # Бесплатный заказ
        mark_order_paid(order_id)
        
        await bot.send_message(
            order.user_id,
            f"🆓 <b>ЗАКАЗ №{order_id} ПРИНЯТ БЕСПЛАТНО!</b>\n\n"
            f"Разработчик начал работу!",
            reply_markup=get_client_order_keyboard(order_id),
            parse_mode="HTML"
        )
        
        await callback.message.edit_text(f"✅ Заказ #{order_id} принят БЕСПЛАТНО!")
        
        # Уведомление админу о старте разработки
        await bot.send_message(
            ADMIN_ID,
            f"🆓 Бесплатный заказ #{order_id} принят. Можно начинать разработку.",
            reply_markup=get_development_keyboard(order_id),
            parse_mode="HTML"
        )
    else:
        # Платный заказ - создаем счет
        order.status = 'waiting_payment'
        
        # Создаем счет на оплату звездами
        prices = [LabeledPrice(label=f"Заказ #{order_id} - {order.tariff.value[0]}", amount=order.tariff.value[1])]
        
        await bot.send_invoice(
            chat_id=order.user_id,
            title=f"Оплата заказа #{order_id}",
            description=f"Тариф: {order.tariff.value[0]}\nОписание: {order.description[:50]}...",
            payload=f"order_{order_id}",
            provider_token="",  # Для звезд оставляем пусто
            currency="XTR",  # Специальная валюта для звезд Telegram
            prices=prices,
            reply_markup=None  # Кнопка оплаты будет в самом счете
        )
        
        await callback.message.edit_text(f"✅ Заказ #{order_id} принят, счет отправлен клиенту")
        
        # Сообщение админу
        await bot.send_message(
            ADMIN_ID,
            f"💰 Заказ #{order_id} принят. Ожидаем оплату от @{order.username}",
            parse_mode="HTML"
        )

# ✅ Pre-checkout запрос - ОБЯЗАТЕЛЬНО подтверждаем
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery, bot):
    """Автоматически подтверждаем pre-checkout запрос"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    print(f"✅ Pre-checkout подтвержден для заказа {pre_checkout_query.invoice_payload}")

# ✅ Обработчик успешной оплаты
async def successful_payment_handler(message: Message, bot):
    """Обработчик успешной оплаты - срабатывает ТОЛЬКО при реальной оплате звездами"""
    payload = message.successful_payment.invoice_payload
    order_id = int(payload.split("_")[1])
    total_amount = message.successful_payment.total_amount
    
    # Помечаем заказ как оплаченный
    mark_order_paid(order_id)
    order = get_order(order_id)
    
    # Сообщение клиенту
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
    
    # Уведомление админу
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

async def reject_order(callback: CallbackQuery, bot):
    """Админ отклоняет заказ"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)
    
    if order:
        # Уведомляем клиента
        await bot.send_message(
            order.user_id,
            f"❌ <b>ЗАКАЗ №{order_id} ОТКЛОНЕН</b>\n\n"
            f"К сожалению, разработчик не может принять этот заказ.\n"
            f"Попробуйте оформить заказ с другим описанием.",
            parse_mode="HTML"
        )
        
        # Удаляем заказ из базы
        from database import orders
        if order_id in orders:
            del orders[order_id]
    
    await callback.message.edit_text(f"❌ Заказ #{order_id} отклонен")

# === ТЕСТОВАЯ ФУНКЦИЯ ДЛЯ ПРОВЕРКИ ОПЛАТЫ ===
async def test_payment(callback: CallbackQuery, bot):
    """Тестовая оплата (для проверки)"""
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="🔧 ТЕСТОВЫЙ ПЛАТЕЖ",
        description="Проверка работы оплаты звездами",
        payload="test_payment",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Тест", amount=1)]
    )

def register_handlers(dp):
    """Регистрация обработчиков оплаты"""
    dp.callback_query.register(accept_order, F.data.startswith("accept_"))
    dp.callback_query.register(reject_order, F.data.startswith("reject_"))
    dp.callback_query.register(test_payment, F.data == "test_payment")  # Тестовая кнопка
    dp.pre_checkout_query.register(pre_checkout_handler)
    dp.message.register(successful_payment_handler, F.successful_payment)
