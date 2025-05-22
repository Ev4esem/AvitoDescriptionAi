import requests

def generate_description_from_openai(prompt, api_key):
    """Генерация описания с использованием OpenAI API"""
    url = 'https://api.openai.com/v1/chat/completions'
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'system', 'content': 'Ты помогаешь с написанием текстов для объявлений на Авито, используя данные о запчастях.'},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7,
        'max_tokens': 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result.get('choices') and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        else:
            return "Ошибка: пустой ответ от OpenAI."
    except Exception as e:
        print(f"Ошибка при обращении к OpenAI: {str(e)}")
        return f"Ошибка при обращении к OpenAI: {str(e)}"

def create_description_prompt(brand, original_part, search_result, applicability_result, oem_result):
    """Создание промпта для генерации описания с уже подготовленными данными"""
    
    # Данные уже в нужном формате, просто извлекаем их
    article_details = search_result.get("data", {}).get("list", [])
    name_part = ""
    if article_details:
        name_part = article_details[0].get("ART_PRODUCT_NAME", "")
    
    # OEM номера уже в нужном формате
    oems = [item.get("ARL_NUMBER", "") for item in oem_result.get("data", {}).get("list", [])]
    
    # Применимость уже в нужном формате
    applicabilities = [item.get("NAME", "") for item in applicability_result.get("data", {}).get("list", [])]
    
    # Формируем аналоги
    articles = "\n".join([f"{item.get('ART_ARTICLE_NR', '')} ({item.get('SUP_BRAND', '')})" for item in article_details])
    
    # Список автомобилей
    cars_list = "\n".join(applicabilities)
    
    # Список OEM номеров
    oems_text = ", ".join(oems)
    
    # Формируем промпт
    prompt = (
        "Напиши продающее и привлекательное описание автозапчасти для Авито с учетом всех параметров. "
        "Используя следующую информацию:\n"
        f"1. **Название**: Сделай точечное хорошее название, чтоб алгоритмы авито считывали его хорошо \"{name_part} для {brand} {original_part}\". \n\n"
        f"2. Цена: за 1 штуку здесь цену не надо писать просто так же оставляешь\n\n"
        f"3. Описание: Напиши, что это новая автозапчасть. Пример: \"Новая, оригинальная запчасть, не использовалась.\"\n\n"
        f"4. Номер запчасти: Укажи артикул, например, {original_part}.\n\n"
        f"5. Кросс-номера: {oems_text}. \n\n"
        f"6. Аналоги: {articles}\n\n"
        f"7. Применимость:\n"
        f"    Перечисли все автомобили, для которых эта запчасть подходит. Пример:\n"
        f"    \"Подходит на автомобили: \n"
        f"    {cars_list}\"\n\n"
        f"8. Условия:\n"
        f"    - 🚗 **Автозапчасти с подбором по VIN** + установка в сервисе (в 10 м от нас).\n"
        f"    - 🛠 **Гарантия до 6 месяцев** и возврат в течение 14 дней.\n"
        f"    - 🚛 **Отправка в день заказа** | Курьером по Москве — за 1 час, по регионам — в день заказа!\n"
        f"    - 💵 **Оплата для ИП и ООО**: Без НДС +6%, С НДС +26%.\n"
        f"    - 🔧 **Установка в сервисе**: Быстрая и качественная установка запчастей.\n"
        f"    - 🔑 **Подбор запчастей по VIN**: Подберите нужные запчасти за несколько минут, просто предоставив нам VIN-код автомобиля.\n"
        f"    - 🏆 **Отзывы**: Мы гордимся высокими оценками и положительными отзывами от наших клиентов.\n\n"
        f"9. Поддержка:\n"
        f"    ✅ Мы компания **DriveLine, предлагаем вам запчасти напрямую от поставщиков — без посредников. \n"
        f"    Поддержка на всем сроке использования.\n\n"
        f"10. Адреса магазинов:\n"
        f"    - 📍 **Кунцевский авторынок, Южная сторона, Автокит А1** (ул. Московская, с12)\n"
        f"    - 📍 **Каширское шоссе 61к3а** (Москва, ТЦ \"ТЯНЬЯ\", 0 этаж, Линия В, Павильон В, 29)\n\n"
        f"11. Режим работы: ежедневно с 10:00 до 19:00 (по просьбе можем задержаться).\n\n"
        f"12. Дополнительные ключевые слова: Процесс подбора, разборки, оригинальные запчасти, замены, трос натяжителя, Mercedes-Benz, тормоза, кузовные детали, доступные запчасти для ремонта.\n\n"
        f"Дополнительные рекомендации**:\n"
        f"    - Пожалуйста, добавь синонимы, такие как \"трос натяжителя\", \"ремень генератора\", \"натяжитель ремня\" для улучшения поисковой выдачи.\n"
        f"    - Постарайся делать описание коротким, но информативным, чтобы оно легко воспринималось и приводило к продажам."
    )
    
    return prompt

def generate_description_from_prompt(brand, original_part, search_result, applicability_result, oem_result, api_key):
    """Функция для использования через инструмент LangChain"""
    prompt = create_description_prompt(brand, original_part, search_result, applicability_result, oem_result)
    return generate_description_from_openai(prompt, api_key)