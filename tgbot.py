import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from google import genai
from google.genai.errors import APIError

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ====================================================================
# ⚠️ ВАЖНО: ВСТАВЬТЕ ВАШИ КЛЮЧИ СЮДА
# ====================================================================
TELEGRAM_TOKEN = "8454613915:AAFP79UgbFN_9oK3d_uhcnxo1We4b5VSla4" 
GEMINI_API_KEY = "AIzaSyDuRJ6SBt7_gTbgQ15KlckbQfyrCA-S41c"
# ====================================================================

# 1. Определение состояний (State Machine)
(
    ASK_CAMERA,
    ASK_BUDGET,
    ASK_PRIORITY,
    ASK_SIZE,
    ASK_OS,
    ASK_ECOSYSTEM,
    ASK_ADD,
    END,
) = range(8)

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logging.error(
        "ОШИБКА: Ключи TELEGRAM_TOKEN или GEMINI_API_KEY не указаны в коде. Пожалуйста, вставьте их."
    )
    exit()

try:
    # Инициализация клиента Gemini с явным указанием ключа
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) 
except Exception as e:
    logging.error(f"Ошибка инициализации Gemini клиента: {e}")
    exit()


# ------------------------------------
# 2. ФУНКЦИИ ДЛЯ СОЗДАНИЯ КЛАВИАТУР
# ------------------------------------

def get_purpose_keyboard():
    """Выбор: для соц сетей, для работы, просто чтоб звонить, для игр, без разницы"""
    keyboard = [
        [InlineKeyboardButton("Соцсети", callback_data="Соцсети")],
        [InlineKeyboardButton("Работа", callback_data="Работа")],
        [InlineKeyboardButton("Просто звонить", callback_data="Звонки")],
        [InlineKeyboardButton("Для игр", callback_data="Игры")],
        [InlineKeyboardButton("Не важно", callback_data="Не важно")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_camera_keyboard():
    """Клавиатура с цифрами от 1 до 10"""
    row1 = [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(1, 6)]
    row2 = [InlineKeyboardButton(str(i), callback_data=str(i)) for i in range(6, 11)]
    return InlineKeyboardMarkup([row1, row2])

def get_budget_keyboard():
    """Варианты бюджета"""
    keyboard = [
        [InlineKeyboardButton("< 10 000 ₽", callback_data="до 10000")],
        [InlineKeyboardButton("10 000 - 25 000 ₽", callback_data="10000-25000")],
        [InlineKeyboardButton("25 000 - 45 000 ₽", callback_data="25000-45000")],
        [InlineKeyboardButton("45 000 - 75 000 ₽", callback_data="45000-75000")],
        [InlineKeyboardButton("> 75 000 ₽", callback_data="от 75000")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_priority_keyboard():
    """Варианты приоритетов"""
    keyboard = [
        [InlineKeyboardButton("Удобство", callback_data="Удобство"),
         InlineKeyboardButton("Надежность", callback_data="Надежность")],
        [InlineKeyboardButton("Игры хорошо тянул", callback_data="Производительность в играх")],
        [InlineKeyboardButton("Хорошая камера", callback_data="Камера"),
         InlineKeyboardButton("Хорошо ловил связь", callback_data="Качество связи")],
        [InlineKeyboardButton("Совместимость с экосистемой", callback_data="Экосистема")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_size_keyboard():
    """Размер телефона"""
    keyboard = [
        [InlineKeyboardButton("Маленький", callback_data="Маленький")],
        [InlineKeyboardButton("Средний", callback_data="Средний")],
        [InlineKeyboardButton("Больше среднего", callback_data="Больше среднего")],
        [InlineKeyboardButton("Большой", callback_data="Большой")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_os_keyboard():
    """Операционная система"""
    keyboard = [
        [InlineKeyboardButton("iOS (Apple)", callback_data="iOS")],
        [InlineKeyboardButton("Android", callback_data="Android")],
        [InlineKeyboardButton("HarmonyOS (Huawei)", callback_data="HarmonyOS")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ecosystem_keyboard():
    """Популярные бренды с экосистемами"""
    keyboard = [
        [InlineKeyboardButton("Apple", callback_data="Apple")],
        [InlineKeyboardButton("Samsung", callback_data="Samsung")],
        [InlineKeyboardButton("Xiaomi/Mi", callback_data="Xiaomi")],
        [InlineKeyboardButton("Huawei/Honor", callback_data="Huawei")],
        [InlineKeyboardButton("Нет других устройств", callback_data="Нет")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ------------------------------------
# 3. ХЕНДЛЕРЫ ДИАЛОГА
# ------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает команду /start и начинает диалог (вопрос 1)"""
    context.user_data.clear() 

    question = "🤖 Привет! Я твой личный консультант по подбору телефонов на базе Gemini. Начнем. \n\n<b>1. Для чего вы собираетесь использовать телефон?</b>"
    
    await update.message.reply_text(
        question, 
        reply_markup=get_purpose_keyboard(),
        parse_mode="HTML"
    )
    return ASK_CAMERA

async def ask_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вопрос 2: Важность камеры"""
    query = update.callback_query
    await query.answer()
    context.user_data["purpose"] = query.data 

    await query.edit_message_text(
        text=f"1. Цель: <b>{query.data}</b>\n\n<b>2. На сколько вам важно качество съемки?</b> (От 1 до 10)",
        reply_markup=get_camera_keyboard(),
        parse_mode="HTML"
    )
    return ASK_BUDGET

async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вопрос 3: Бюджет"""
    query = update.callback_query
    await query.answer()
    context.user_data["camera_importance"] = query.data 

    await query.edit_message_text(
        text=f"2. Важность камеры: <b>{query.data} из 10</b>\n\n<b>3. В каком бюджете вы рассматриваете телефон?</b> (примерные диапазоны)",
        reply_markup=get_budget_keyboard(),
        parse_mode="HTML"
    )
    return ASK_PRIORITY

async def ask_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вопрос 4: Приоритеты"""
    query = update.callback_query
    await query.answer()
    context.user_data["budget"] = query.data

    await query.edit_message_text(
        text=f"3. Бюджет: <b>{query.data}</b>\n\n<b>4. Что для вас самое важное в телефоне?</b>",
        reply_markup=get_priority_keyboard(),
        parse_mode="HTML"
    )
    return ASK_SIZE

async def ask_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вопрос 5: Размер телефона"""
    query = update.callback_query
    await query.answer()
    context.user_data["priority"] = query.data

    await query.edit_message_text(
        text=f"4. Приоритет: <b>{query.data}</b>\n\n<b>5. Какого размера телефон вы рассматриваете?</b>",
        reply_markup=get_size_keyboard(),
        parse_mode="HTML"
    )
    return ASK_OS

async def ask_os(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вопрос 6: Операционная система"""
    query = update.callback_query
    await query.answer()
    context.user_data["size"] = query.data

    await query.edit_message_text(
        text=f"5. Размер: <b>{query.data}</b>\n\n<b>6. Какую операционную систему вы бы предпочли?</b>",
        reply_markup=get_os_keyboard(),
        parse_mode="HTML"
    )
    return ASK_ECOSYSTEM

async def ask_ecosystem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вопрос 7: Текущая экосистема"""
    query = update.callback_query
    await query.answer()
    context.user_data["Os"] = query.data

    await query.edit_message_text(
        text=f"6. ОС: <b>{query.data}</b>\n\n<b>7. Устройствами от каких компаний вы пользуетесь?</b> (Это поможет проверить совместимость)",
        reply_markup=get_ecosystem_keyboard(),
        parse_mode="HTML"
    )
    return ASK_ADD

async def ask_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Вопрос 8: Дополнительная информация (текстовый ввод)"""
    query = update.callback_query
    await query.answer()
    context.user_data["ecosystem"] = query.data

    await query.edit_message_text(
        text=f"7. Экосистема: <b>{query.data}</b>\n\n<b>8. Что бы вы еще хотели уточнить при выборе телефона?</b> (Напишите текстом, если нечего добавить, напишите 'Нет').",
        parse_mode="HTML"
    )
    
    return END

async def send_to_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Последний шаг: собирает данные, формирует промпт и вызывает Gemini API"""

    user_add = update.message.text if update.message.text else "Ничего не уточнено."
    context.user_data["add"] = user_add

    data = context.user_data
    
    await update.message.reply_text("🧠 <b>Отлично, данные собраны!</b> \n\n<i>Идет подбор 5 лучших моделей с кратким описанием...</i>", parse_mode="HTML")

    # Формирование промпта
    prompt = f"""Представь что ты самый лучший консультант в мире и подбери телефон для клиента используя эти параметры:
Я собираюсь использовать телефон для: {data.get('purpose', 'Не указано')},
Для меня качество съемки важно на: {data.get('camera_importance', '5')} из 10,
Я рассматриваю телефон в бюджете примерно: {data.get('budget', 'Средний')},
Для меня в телефоне самое важное это: {data.get('priority', 'Не указано')},
Я хотел бы телефон размера: {data.get('size', 'Средний')},
Я бы хотел телефон с операционной системой: {data.get('Os', 'Не указано')}. Предложи устройства с не только этой системой, если это логично.
Так же у меня есть устройства от компании: {data.get('ecosystem', 'Нет')}. Учти возможность создания экосистемы.
Так же возми во внимание, что я бы хотел: {data.get('add', 'Нет дополнительных пожеланий')}.

Найди и представь в виде маркированного списка 5 моделей с кратким их описанием исходя из отзывов пользователей. Предоставь только список и описание, без вводных фраз и заключений.
"""

    try:
        # Вызов Gemini API
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        # === РЕАЛИЗАЦИЯ ВАРИАНТА 2: HTML-ПАРСИНГ ДЛЯ НАДЕЖНОСТИ ===
        
        # 1. Заменяем жирный Markdown (**текст**) на жирный HTML (<b>текст</b>)
        # Это помогает избежать ошибок парсинга Markdown в Telegram.
        # Используем простую замену, что достаточно для большинства ответов Gemini.
        formatted_text = response.text.replace('**', '<b>').replace('<b>', '</b>', 1) 
        # Дополнительно экранируем символы < и > для предотвращения проблем с HTML
        formatted_text = formatted_text.replace('<', '&lt;').replace('>', '&gt;').replace('<b>', '<b>').replace('</b>', '</b>')
        
        # Заголовок также делаем HTML
        result_text = f"✅ <b>Результат подбора от консультанта Gemini:</b>\n\n{formatted_text}"

        # 2. Отправка результата пользователю с parse_mode="HTML"
        await update.message.reply_text(result_text, parse_mode="HTML")

    except APIError as e:
        error_message = f"❌ <b>Ошибка API:</b> Произошла ошибка при обращении к Gemini. Убедитесь, что ваш API ключ верен. Детали: <code>{e.response.status_code}</code>"
        await update.message.reply_text(error_message, parse_mode="HTML")
    except Exception as e:
        # Обработка ошибки парсинга (если она все же произошла)
        error_message = f"❌ <b>Общая ошибка:</b> Не удалось получить ответ от Gemini. {e}"
        await update.message.reply_text(error_message, parse_mode="HTML")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает команду /cancel и завершает диалог"""
    await update.message.reply_text(
        'Консультация прервана. Начните снова с команды /start.',
    )
    return ConversationHandler.END


# ------------------------------------
# 4. ОСНОВНАЯ ФУНКЦИЯ ЗАПУСКА
# ------------------------------------

def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_CAMERA: [CallbackQueryHandler(ask_camera)],
            ASK_BUDGET: [CallbackQueryHandler(ask_budget)],
            ASK_PRIORITY: [CallbackQueryHandler(ask_priority)],
            ASK_SIZE: [CallbackQueryHandler(ask_size)],
            ASK_OS: [CallbackQueryHandler(ask_os)],
            ASK_ECOSYSTEM: [CallbackQueryHandler(ask_ecosystem)],
            ASK_ADD: [CallbackQueryHandler(ask_add)],
            END: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_to_gemini)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    logging.info("🚀 Бот запущен! Ожидание команды /start...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()