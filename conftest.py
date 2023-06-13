import pytest
from selenium import webdriver

'''
Я не стала усложнять структуру проекта
указанием в conftest.py ссылок на файлы с фикстурами
pytest_plugins = [
    'fixtures',
]

и, собственно, самим файлом с фикстурами, кажется, что здесь это излишне
'''


# используем scope 'session', чтобы браузер не закрывался между тестами
# так же задаю параметры на кросс-браузерное тестирование,
# с Firefox работает очень нестабильно, часто отваливается по таймауту,
# потому что не может загрузить google.com и другие страницы гугла, не пойму, в чём дело,
# но, если такое произошло, просто запустите тесты ещё раз
@pytest.fixture(params=['chrome', 'firefox'], scope='session')
def browser(request):
    if request.param == 'chrome':
        # Создание экземпляра браузера Chrome
        driver = webdriver.Chrome()
    elif request.param == 'firefox':
        # Создание экземпляра браузера Firefox
        driver = webdriver.Firefox()
    else:
        raise ValueError(f'Unsupported browser: {request.param}')

    yield driver

    # Закрытие браузера после выполнения всех тестов
    driver.quit()
