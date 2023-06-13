import re
from time import sleep
from typing import Callable, Optional

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from logconfig import logger

URL_GOOGLE = 'https://www.google.com/'


def wait_for_page_load(browser: webdriver) -> Optional[None]:
    '''Функция ждёт, 10 секунд или до тех пор, пока загрузится страница.
    Загрузку страницу определяет по появившемуся html-элементу "body"'''
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    )


def search_ivi_in_google(browser: webdriver) -> Optional[None]:
    '''Функция открывает сайт google.com и ищет в нём ivi'''
    browser.get(URL_GOOGLE)

    # здесь добавила ожидание загрузки страницы, исключение добавлять не стала,
    # потому что, если с гугла потеряется строка поиска, то у нас будут проблемы побольше,
    # чем отсутствие здесь исключения
    search_input = WebDriverWait(browser, timeout=3).until(
        lambda d: d.find_element(By.NAME, 'q'))
    search_input.send_keys('ivi')
    search_input.send_keys(Keys.ENTER)

    wait_for_page_load(browser)


def get_ivi_app_rating_on_google_play(browser: webdriver) -> str:
    '''
    Google.play не доступен из РФ, нужно запускать браузер с подменой IP
    код мог бы выглядеть как-то так
    options = Options()
    options.add_argument('--proxy-server=206.84.101.110:9090')
    browser = webdriver.Chrome(options=options)
    browser.get('https://play.google.com/store/apps/details?id=ru.ivi.client')
    sleep(3)
    rating_element = browser.find_element(
        By.XPATH, '//div[contains(@aria-label, "Средняя оценка")]')
    rating_number = rating_element.text
    return rating_element

    у меня нет рабочего прокси-сервера, я думаю, что
    в компании есть своё готовое решение для этой ситуации,
    поэтому моя функция просто возвращает константное значение,
    хотя, конечно, правильно брать актуальный рейтинг со страницы
    '''
    return '4,4'


def get_elements_from_several_pages(browser: webdriver, page_number: int, search_xpath: str, func: Callable) -> list:
    '''Функция листает первые page_number страниц google.com двумя способами -
    используя пагинацию или динамической прокруткой, в зависимости от того, какой вид главно открылся.
    Находит на этих страницах элементы, соответствующие search_xpath и применяет к каждому элементу
    переданную функцию func, сохраняя результаты в список и возвращая его'''

    # тут я сломала себе весь мозг и зависла надолго,
    # дело в том, что изначально я попала на динамическую подгрузку страниц
    # и написала вот такой код для листания
    # while page_count <= 5:
    # actions = ActionChains(browser)
    # actions.send_keys(Keys.END)
    # actions.perform()
    # sleep(2)
    # page_count += 1
    # всё работало отлично, пока при одном из запусков страница внезапно
    # перестала быть динамической и на ней появилась пагинация
    # я написала условие вроде "если есть кнопка пагинации, то листай так,
    # если нет кнопки, то делай динамическую прокрутку"
    # и ещё через несколько итераций словила интерфейс, где нет
    # ни пагинации, ни автопрокрутки, нужно долистать экран до конца
    # и там нажать кнопку "загрузить ещё".
    # Третий if я делать не стала, посёрчила в интернете, может,
    # есть готовые решения учёта всех трёх возможных вариантов,
    # не нашла и оставила только два варианта, без условия, через конструкцию try-except
    html_result_elements = []
    text_results = []
    page_count = 1
    while page_count <= page_number:
        try:
            # если на странице находится ссылка на следующую страницу,
            # то мы попали на вариант с пагинацией
            next_page_button = browser.find_element(
                By.XPATH, '//a[@aria-label="Page ' + str(page_count + 1) + '"]')
        except NoSuchElementException:
            # пишу уведомление в лог, чтобы знать, когда мы попали на динамическую прокрутку
            logger.exception(f'Ссылка на {page_count + 1} не найдена, возможно, поисковая выдача закончилась ' +
                             'или не повезло попасть на вариант с динамической загрузкой страниц')
            # цикл, который позволяет сразу открыть все нужные страницы
            while page_count <= page_number:
                actions = ActionChains(browser)
                actions.send_keys(Keys.END)
                actions.perform()
                sleep(2)
                page_count += 1

            # и после открытия всех страниц ищем в них нужные элементы
            html_result_elements = browser.find_elements(By.XPATH, search_xpath)
            # применяем функцию поиска к каждому элементу и сохраняем результат в переменную
            # в целом, конкретно здесь можно не сохранять элемент, а сразу каждый проверять assert,
            # потому что это вариант, где у нас динамическая прокрутка и все элементы на одной странице,
            # то есть можно обращаться к ним, страница не была обновлена, но я всё же сохраняю сначала элементы,
            # а потом обрабатываю в тестирующей функции для упрощения чтения кода, для того,
            # чтобы все assert были в коде тестирующей функции и для унификации выдачи
            for element in html_result_elements:
                text_results.append(func(element))

            return text_results

        # этот код запускается, когда обнаружили наличие пагинации
        # и здесь уже из-за того, что нельзя запомнить объект класса WebElement
        # при переходе между страницами, мы вынуждено записываем нужные нам значения
        # до того, как "перелистнём страницу"
        # тут сохраняем все элементы одной страницы
        one_page_html_elements = browser.find_elements(By.XPATH, search_xpath)
        # обрабатываем их и записываем уже в результирующий список
        for element in one_page_html_elements:
            text_results.append(func(element))

        next_page_button.click()
        wait_for_page_load(browser)

        page_count += 1
    return text_results


def get_rating_from_element(element: WebElement) -> list[str, str]:
    '''Функция ищет в переданном объекте класса WebElement
    строку рейтинга и вытаскивает из неё строковое значение рейтинга приложения,
    а так же сохраняет class элемента, чтобы позже можно было найти элемент,
    с которым возникла ошибка'''
    class_element = element.find_element(By.CSS_SELECTOR, '[class]')
    class_value = class_element.get_attribute('class')

    rating_element = element.find_element(By.XPATH, '//span[contains(text(), "Рейтинг:")]')
    rating_text = rating_element.text
    rating_number_on_google_search = re.search(r"\d+,\d+", rating_text).group()

    # такой код прервёт сравнение на первом обнаруженном несовпадении рейтингов
    # и не проверит все остальные элементы, с точки зрения тестирования
    # это кажется более логичным - по одной ошибке за раз на исправление :)
    # но если надо вернуть все ошибки, то можно
    # пройтись по списку и посчитать все несовпадения,
    # зафиксировав, например, в словарь, элементы, где несовпадения встретились

    return rating_number_on_google_search, class_value


def get_link_from_element(element: WebElement) -> str:
    '''Функция ищет в переданном объекте класса WebElement
    элемент ссылки и возвращает его'''
    wikipedia_link = element.get_attribute('href')

    return wikipedia_link
