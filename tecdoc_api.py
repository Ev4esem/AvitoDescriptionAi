import requests
import re

def search_part_wrapper(args):
    """
    Обертка для первого поиска - только по артикулу, извлекает SUP_ID и SUP_BRAND.
    """
    # На первом шаге всегда ищем только по артикулу
    result = search_part(args)  # Передаем только part_number
    
    # Создаем простой ответ только с SUP_ID и SUP_BRAND
    simplified_result = {"success": True, "data": {"list": []}}
    
    if result.get("data") and result["data"].get("list"):
        for item in result["data"]["list"]:
            simplified_item = {
                "SUP_ID": item.get("SUP_ID", ""),
                "SUP_BRAND": item.get("SUP_BRAND", "")
            }
            simplified_result["data"]["list"].append(simplified_item)
    
    return simplified_result

def search_part(part_number):
    """Поиск запчасти по номеру артикула"""
    server_url = "http://62.109.23.215:3000"
    url = f"{server_url}/tecdoc-search?search_number={part_number}"
    
    print(f"Запрос: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка при запросе для части {part_number}: {str(e)}")
        return {"error": str(e), "data": {"list": []}}

def search_part_with_sup_id_wrapper(args):
    """Обертка для search_part_with_sup_id, обрабатывающая строку с запятыми"""
    parts = parse_comma_args(args, 3)
    if len(parts) >= 3:
        return search_part_with_sup_id(parts[0], parts[1], parts[2])
    elif len(parts) == 2:
        return search_part_with_sup_id(parts[0], parts[1])
    return {"error": "Недостаточно аргументов", "data": {"list": []}}

def search_part_with_sup_id(part_number, sup_id, sup_brand):
    """Поиск запчасти по номеру артикула, SUP_ID и SUP_BRAND"""
    server_url = "http://62.109.23.215:3000"
    url = f"{server_url}/tecdoc-search?search_number={part_number}&sup_id={sup_id}&sup_code={sup_brand}&with_price_only=false&oem=false&oem_search_limit=5"
    print(f"Запрос с SUP_ID: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка при запросе с SUP_ID для части {part_number}: {str(e)}")
        return {"error": str(e), "data": {"list": []}}

def get_oem_part_wrapper(args):
    """
    Обертка для get_oem_part, извлекающая только ARL_NUMBER.
    """
    if isinstance(args, str):
        result = get_oem_part(args)
        
        # Создаем упрощенный ответ только с ARL_NUMBER
        simplified_result = {"success": True, "data": {"list": []}}
        
        if result.get("data") and result["data"].get("list"):
            for item in result["data"]["list"]:
                if item.get("ARL_NUMBER"):
                    simplified_result["data"]["list"].append({"ARL_NUMBER": item["ARL_NUMBER"]})
        
        return simplified_result
    
    return {"error": "Неверный формат аргумента", "data": {"list": []}}

def get_oem_part(art_id):
    """Получение оригинальных артикулов"""
    server_url = "http://62.109.23.215:3000"
    url = f"{server_url}/tecdoc-oem?art_id={art_id}"
    
    print(f"Запрос OEM: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка при запросе OEM для артикула: {str(e)}")
        return {"error": str(e), "data": {"list": []}}

def get_applicability_wrapper(args):
    """Обертка для get_applicability, обрабатывающая строку с запятыми"""
    parts = parse_comma_args(args, 3)
    if len(parts) >= 3:
        if not parts[0] or parts[0] == '0' or parts[0].lower() == 'none':
            return {
                "error": "ART_ID не может быть пустым, 'None' или равным '0'",
                "data": {"list": []}
            }
        return get_applicability(parts[0], parts[1], parts[2])
    return {"error": "Недостаточно аргументов", "data": {"list": []}}

def get_applicability(art_id, art_article_nr, sup_brand):
    """Получение применимости запчасти к автомобилям (только названия)"""
    server_url = "http://62.109.23.215:3000"
    url = f"{server_url}/tecdoc-applicability?art_id={art_id}&article={art_article_nr}&brand={sup_brand}"
    
    print(f"Запрос применимости: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        full_data = response.json()
        
        # Извлекаем только названия, ограничиваем до 15 штук
        names = []
        if full_data.get("data", {}).get("list"):
            names = [item.get("NAME", "") for item in full_data["data"]["list"][:30]]
            names = [name for name in names if name]  # Убираем пустые
        
        return {
            "success": True,
            "data": {"list": [{"NAME": name} for name in names]}
        }
        
    except Exception as e:
        print(f"Ошибка при запросе применимости: {str(e)}")
        return {"error": str(e), "data": {"list": []}}

def clean_part_number(part_number):
    """Очистка артикула от нецифровых символов"""
    return re.sub(r'[^\d]', '', part_number)

def parse_comma_args(args_str, count=None):
    """
    Разбирает строку с аргументами, разделенными запятыми.
    Возвращает список аргументов.
    """
    if isinstance(args_str, str) and "," in args_str:
        parts = [part.strip() for part in args_str.split(",")]
        if count is not None and len(parts) >= count:
            return parts[:count]  # Возвращаем только нужное количество аргументов
        return parts
    return [args_str]  # Возвращаем одиночный аргумент в списке

def parse_comma_args(args_str, count=None):
    """
    Разбирает строку с аргументами, разделенными запятыми.
    Возвращает список аргументов.
    
    Args:
        args_str: Строка с аргументами через запятую или одиночный аргумент
        count: Максимальное количество аргументов для возврата (если указано)
    
    Returns:
        Список аргументов
    """
    if isinstance(args_str, str) and "," in args_str:
        parts = [part.strip() for part in args_str.split(",")]
        if count is not None and len(parts) >= count:
            return parts[:count]  # Возвращаем только нужное количество аргументов
        return parts
    return [args_str] 