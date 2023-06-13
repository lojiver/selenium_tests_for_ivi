import logging

'''Делала, в основном, для своих целей отладки и,
чтобы показать, что я верхнеуровнево знаю про возможности модуля logging'''

# создаём экземпляр класса logging
logger = logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

# использую встроенный обработчик для записи в файл,
# параметр mode='w' перезаписывает зайл при каждом запуске программы
handler = logging.FileHandler('google_search_ivi.log', mode='w', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(funcName)s - %(message)s'
)

handler.setFormatter(formatter)
logger.addHandler(handler)
