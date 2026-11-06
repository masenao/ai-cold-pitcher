import os
import streamlit as st
import google.generativeai as genai

# Настройка страницы
st.set_page_config(
    page_title="Генератор холодных сообщений",
    page_icon="📩",
    layout="centered"
)

# Заголовок и описание
st.title("📩 Генератор холодных сообщений")
st.markdown(
    "Создавайте краткие, персонализированные предложения для бизнеса с помощью Google Gemini."
)

# Боковая панель (Sidebar)
st.sidebar.header("🔑 Настройки API и модели")

api_key = st.sidebar.text_input(
    "Введите Gemini API Key:",
    type="password",
    help="Получить ключ можно на https://aistudio.google.com/"
)

# Настройка прокси (на случай блокировки по региону в РФ/РБ)
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Сеть и прокси")
proxy = st.sidebar.text_input(
    "HTTP/HTTPS Прокси (опционально):",
    placeholder="http://127.0.0.1:10808",
    help="Заполните, если запросы к Gemini блокируются в вашем регионе и нет системного VPN."
)

if proxy.strip():
    os.environ["HTTP_PROXY"] = proxy.strip()
    os.environ["HTTPS_PROXY"] = proxy.strip()
else:
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Выбор модели")

# Актуальные реально существующие модели в Google AI Studio
DEFAULT_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-thinking-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

if "available_models" not in st.session_state:
    st.session_state["available_models"] = DEFAULT_MODELS

# Кнопка обновления списка прямо из Google API
if st.sidebar.button("🔄 Загрузить модели из аккаунта", use_container_width=True):
    if not api_key:
        st.sidebar.error("Сначала введите API-ключ выше!")
    else:
        with st.spinner("Опрашиваем Google API..."):
            try:
                # Используем REST вместо gRPC с таймаутом
                genai.configure(api_key=api_key, transport="rest")
                fetched = [
                    m.name.replace("models/", "")
                    for m in genai.list_models(request_options={"timeout": 15})
                    if "generateContent" in m.supported_generation_methods
                ]
                if fetched:
                    st.session_state["available_models"] = fetched
                    st.sidebar.success(f"Загружено моделей: {len(fetched)}")
                else:
                    st.sidebar.warning("Список пуст (проверьте VPN/регион).")
            except Exception as ex:
                st.sidebar.error(f"Ошибка получения списка: {ex}")

# Выпадающий список моделей + возможность ввести вручную
model_options = list(st.session_state["available_models"])
if "Ввести вручную..." not in model_options:
    model_options.append("Ввести вручную...")

selected_option = st.sidebar.selectbox(
    "Выберите модель:",
    options=model_options,
    index=0,
    help="Рекомендуется gemini-2.0-flash — самая быстрая и актуальная модель в Google AI Studio."
)

if selected_option == "Ввести вручную...":
    model_name = st.sidebar.text_input(
        "Введите точное название модели:",
        value="gemini-2.0-flash",
        placeholder="Например: gemini-2.0-flash"
    )
else:
    model_name = selected_option

st.sidebar.markdown("---")
st.sidebar.markdown(
    "👉 **Инструкция:**\n"
    "1. Вставьте ключ Gemini API в сайдбар.\n"
    "2. Если вы в РФ/РБ — **включите системный VPN** (или укажите прокси).\n"
    "3. Заполните форму и нажмите кнопку генерации."
)

# Инициализация состояния для сохранения результата
if "generated_text" not in st.session_state:
    st.session_state["generated_text"] = ""

# Главная форма ввода
with st.form("business_form"):
    st.subheader("🏢 Данные о бизнесе")
    
    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input(
            "Название бизнеса",
            placeholder="Например: Кофейня 'Уют' или CleanPro"
        )
    with col2:
        niche = st.text_input(
            "Ниша",
            placeholder="Например: Общепит, клининг, фитнес"
        )
    
    problem = st.text_area(
        "Проблема",
        placeholder="Например: нет сайта, нет системы возврата клиентов, низкая конверсия в запись"
    )
    
    submit_button = st.form_submit_button(
        "✨ Сгенерировать сообщение",
        use_container_width=True
    )

# Обработка нажатия кнопки
if submit_button:
    if not api_key:
        st.sidebar.error("⚠️ Пожалуйста, введите ваш Google Gemini API Key в боковой панели!")
    elif not business_name.strip() or not niche.strip() or not problem.strip():
        st.warning("⚠️ Пожалуйста, заполните все поля формы (Название, Ниша, Проблема).")
    elif not model_name.strip():
        st.warning("⚠️ Пожалуйста, выберите или укажите модель.")
    else:
        with st.spinner(f"🤖 ИИ ({model_name}) генерирует холодное предложение..."):
            try:
                # 1. Используем transport="rest", чтобы избежать бесконечных зависаний gRPC
                genai.configure(api_key=api_key, transport="rest")
                model = genai.GenerativeModel(model_name.strip())
                
                # Формирование промпта: дружелюбно, своими словами, без штампов
                prompt = (
                    f"Напиши короткое, теплое и дружелюбное сообщение владельцу бизнеса (всего 2-3 простых предложения).\n\n"
                    f"Бизнес: {business_name}\n"
                    f"Ниша: {niche}\n"
                    f"Проблема: {problem}\n\n"
                    f"Правила:\n"
                    f"- Пиши простыми словами, легко и по-человечески, как будто пишешь хорошему знакомому в Телеграм.\n"
                    f"- Тон: дружелюбный, спокойный, уважительный и ненавязчивый.\n"
                    f"- СТРОГО ЗАПРЕЩЕНО использовать штампы и маркетинговые слова: 'оцифровать' (или 'о цифровать'), 'кейсы', 'лендинг', 'лиды', 'воронка', 'боли', 'под ключ', 'масштабирование'.\n"
                    f"- Структура: тепло поздоровайся, своими словами и по-доброму укажи на проблему, предложи помочь ее решить и задай один простой вопрос, интересно ли обсудить."
                )
                
                # 2. Устанавливаем жёсткий таймаут 25 секунд — скрипт больше не зависнет!
                response = model.generate_content(
                    prompt,
                    request_options={"timeout": 25}
                )
                
                if response and response.text:
                    st.session_state["generated_text"] = response.text.strip()
                    st.success("Готово! Сообщение успешно создано.")
                else:
                    st.error("Ответ от модели пуст. Попробуйте еще раз.")
            except Exception as e:
                err_text = str(e)
                st.error(f"❌ Произошла ошибка при обращении к API: {err_text}")
                
                # Подробная диагностика частых проблем
                if "404" in err_text or "not found" in err_text.lower():
                    st.warning(
                        f"💡 **Почему модель '{model_name}' не найдена (404 Not Found):**\n\n"
                        "1. **Модели с таким именем нет в публичном API:** В Google AI Studio самые свежие модели — это `gemini-2.0-flash` или `gemini-1.5-flash`. "
                        "Модели `gemini-3.8-flash` в публичном API Google пока не существует (это внутреннее название ассистента в редакторе).\n\n"
                        "2. **Блокировка по региону (РФ / РБ):** "
                        "Если запросы идут с российского IP без VPN, Google скрывает модели и возвращает 404. "
                        "Включите системный VPN или пропишите прокси.\n\n"
                        "3. **Проверьте список:** Нажмите кнопку **«🔄 Загрузить модели из аккаунта»** в сайдбаре слева."
                    )
                elif "timeout" in err_text.lower() or "deadline" in err_text.lower():
                    st.warning(
                        "⌛ **Превышено время ожидания ответа (Timeout):**\n\n"
                        "Запрос не смог дойти до серверов Google за 25 секунд. "
                        "Проверьте работу вашего VPN или прокси-соединения."
                    )

# Блок вывода результата с возможностью быстрого копирования
if st.session_state["generated_text"]:
    st.markdown("### 📋 Готовое сообщение:")
    
    with st.container():
        st.code(st.session_state["generated_text"], language=None)
        st.caption("💡 *Нажмите на значок копирования в правом верхнем углу блока выше, чтобы скопировать текст в буфер обмена.*")
