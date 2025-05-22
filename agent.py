from langchain.agents import AgentType, initialize_agent, Tool
from langchain_openai import ChatOpenAI
from tecdoc_api import (
    search_part_wrapper,                # Используем обертку вместо search_part
    search_part_with_sup_id_wrapper, 
    get_oem_part_wrapper,              # Используем обертку вместо get_oem_part
    get_applicability_wrapper, 
    clean_part_number
)
from description_gen import generate_description_from_prompt

def create_auto_parts_agent(api_key):
    """Создание LangChain агента для обработки автозапчастей"""
    
    # Инициализация языковой модели
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-3.5-turbo",
        api_key=api_key
    )
    
    # Функция-обертка для инструмента generate_description
    def generate_description_tool(brand, original_part, search_result, applicability_result, oem_result):
        try:
            return generate_description_from_prompt(brand, original_part, search_result, applicability_result, oem_result, api_key)
        except Exception as e:
            return f"Ошибка при генерации описания: {str(e)}"

    # Определение инструментов для агента
    tools = [
        Tool(
            name="search_part",
            func=search_part_wrapper,  # Используем обертку
            description="""Первичный поиск запчасти по номеру артикула в базе TecDoc. 
            
            Принимает один аргумент:
            - part_number: номер артикула запчасти (строка)
            
            Возвращает: упрощенный словарь только с SUP_ID и SUP_BRAND."""
        ),
        Tool(
            name="search_part_with_sup_id",
            func=search_part_with_sup_id_wrapper,
            description="""Расширенный поиск запчасти с использованием SUP_ID и SUP_BRAND. 
            
            ВАЖНО: Передавай все параметры одной строкой через запятые:
            search_part_with_sup_id("part_number,sup_id,sup_brand")
            
            Например: search_part_with_sup_id("1987949412,16,BMW")
            
            Возвращает: упрощенный словарь с ART_ID, ART_ARTICLE_NR, SUP_BRAND, ART_PRODUCT_NAME."""
        ),
        Tool(
            name="get_applicability",
            func=get_applicability_wrapper,
            description="""Получение списка автомобилей, для которых подходит запчасть. 
            
            ВАЖНО: Передавай все три параметра ОДНОЙ СТРОКОЙ через запятые:
            get_applicability("art_id,art_article_nr,sup_brand")
            
            Например: get_applicability("123456,1987949412,BOSCH")
            
            Возвращает: упрощенный словарь только с NAME моделей автомобилей."""
        ),
        Tool(
            name="get_oem_part",
            func=get_oem_part_wrapper,  # Используем обертку
            description="""Получение оригинальных (OEM) номеров артикулов для запчасти. 
            
            Принимает один аргумент:
            - art_id: ID артикула из TecDoc (строка)
            
            Возвращает: упрощенный словарь только с ARL_NUMBER номерами."""
        ),
        Tool(
            name="clean_part_number",
            func=clean_part_number,
            description="""Очистка артикула от нецифровых символов (оставляет только цифры). 
            
            Принимает один аргумент:
            - part_number: номер артикула для очистки (строка)
            
            Возвращает: строку, содержащую только цифры из исходного артикула."""
        ),
        Tool(
            name="generate_description",
            func=generate_description_tool,
            description="""Генерация описания для Авито на основе данных о запчасти.
            
            Принимает пять аргументов в следующем порядке:
            - brand: бренд запчасти (строка)
            - original_part: исходный номер артикула (строка)
            - search_result: результат расширенного поиска (упрощенный словарь)
            - applicability_result: результат запроса применимости (упрощенный словарь)
            - oem_result: результат запроса OEM-номеров (упрощенный словарь)
            
            Возвращает: готовое форматированное описание для Авито."""
        )
    ]

    # Создание агента
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=15,
        agent_kwargs={
            "prefix": """Ты опытный инженер, который помогает с автозапчастями. Твоя задача - точно следовать инструкциям и правильно вызывать инструменты.
            КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА ВЫЗОВА ИНСТРУМЕНТОВ:

            1. При вызове инструментов НИКОГДА не используй имена параметров (например, part_number=, art_id=).
            2. Передавай ТОЛЬКО значения без имен параметров.

            Примеры ПРАВИЛЬНЫХ вызовов:
            Action: search_part
            Action Input: 1987949412

            Action: get_oem_part  
            Action Input: 123456

            Action: search_part_with_sup_id
            Action Input: 1987949412,16,BMW

            Action: get_applicability
            Action Input: 123456,1987949412,BOSCH

            Примеры НЕПРАВИЛЬНЫХ вызовов (НЕ ДЕЛАЙ ТАК):
            Action: search_part
            Action Input: part_number=1987949412

            Action: get_oem_part
            Action Input: art_id=123456

            ДОПОЛНИТЕЛЬНЫЕ ИНСТРУКЦИИ:
            - Все инструменты возвращают упрощенные данные только с нужными полями
            - При вызове get_applicability и search_part_with_sup_id передавай параметры ОДНОЙ СТРОКОЙ через запятые  
            - Убедись, что используешь валидные ID для всех запросов
            - Следуй алгоритму шаг за шагом, не пропускай шаги

            ПОМНИ: Передавай только значения, никаких имен параметров!"""
        }
    )
    
    
    return agent