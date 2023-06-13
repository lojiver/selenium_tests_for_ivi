from typing import Optional
import pytest

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from utils import (
    get_elements_from_several_pages, get_ivi_app_rating_on_google_play,
    get_rating_from_element, get_link_from_element,
    search_ivi_in_google, wait_for_page_load)


def test_big_pictures_links_to_ivi(browser: webdriver) -> Optional[None]:
    '''Функция открывает сайт google.com, ищет в нём ivi,
    переходит в "Картинки", фильтрует их по большому размеру и убеждается,
    что не менее трёх больших картинок ведёт на ivi.ru'''
    search_ivi_in_google(browser)

    # Переход в раздел "Картинки"
    try:
        images_link = browser.find_element(By.LINK_TEXT, 'Картинки')
    except NoSuchElementException:
        pytest.fail('Ссылка на "Картинки" не найдена, похоже, элемент сменил свой XPATH')
    images_link.click()

    # Включение фильтра только по большим изображениям (в три клика)
    try:
        instruments = browser.find_element(
            By.XPATH, '//div[@class="PNyWAd ZXJQ7c"]')
    except NoSuchElementException:
        pytest.fail('Ссылка на "Инструменты" не найдена, похоже, элемент сменил свой XPATH')
    instruments.click()

    try:
        size = browser.find_element(By.XPATH, '//div[@class="xFo9P r9PaP"]')
    except NoSuchElementException:
        pytest.fail('Ссылка на "Размер" не найдена, похоже, элемент сменил свой XPATH')
    size.click()

    try:
        big = browser.find_element(By.XPATH, '//a[@aria-label="Большой"]')
    except NoSuchElementException:
        pytest.fail('Ссылка на "Большой" не найдена, похоже, элемент сменил свой XPATH')
    big.click

    # здесь у меня был вопрос - надо найти все ссылки,
    # которые полностью равны www.ivi.ru/ или только содержат этот домен,
    # но код находил всего 2 ссылки чисто на ivi.ru,
    # и я решила искать всё же включения тоже, в норме я, конечно,
    # уточнила бы ТЗ - как надо искать

    # не делаю конструкцию try-except, потому что find_elements
    # возвращается пустой список, если ничего не найдёт,
    # соответственно, программа не сломается и assert отработает,
    # показав ошибку 0 не больше или равно 3
    ivi_links = browser.find_elements(By.XPATH, "//a[contains(@href, 'ivi.ru')]")

    assert len(ivi_links) >= 3, (
        'По запросу ivi.ru в google-картинках найдено менее 3 ссылок на ivi.ru'
    )


def test_first_five_page_google_links_to_google_play(browser: webdriver) -> Optional[None]:
    '''Функция открывает сайт google.com, ищет в нём ivi,
    затем на первых 5 страницах поисковой выдачи находит ссылки на play.google.com
    и сравнивает значение рейтинга приложения в короткой карточке поисковой выдачи
    со значением рейтинга на странице приложения в GP'''

    search_ivi_in_google(browser)

    # передаём сессию браузера, количество страниц, на которых ищем - 5,
    # XPATH, по которому ищем и утилитарную функцию, которая находит рейтинг в
    # каждом найденном эелементе, в store_ratings получаем список вида
    # [['3,5', 'ABC'], ['4,4', 'BCA]], где первый элемент вложенного списка -
    # рейтинг в короткой поисковой карточке, а второй элемент вложенного списка -
    # это уникальный класс элемента, по которому его потом можно при необходимости поискать
    # и исправить
    store_ratings = get_elements_from_several_pages(
        browser, 5, '//a[contains(@href, "play.google.com/store/apps/")]', get_rating_from_element)

    assert len(store_ratings) > 0, (
        'На 5 первых страницах google не найдено ни одной ссылки на play.google.com'
    )

    for rating in store_ratings:
        # такой код прервёт сравнение на первом обнаруженном несовпадении рейтингов
        # и не проверит все остальные элементы, с точки зрения тестирования
        # это кажется более логичным - по одной ошибке за раз на исправление :)
        # но если надо вернуть все ошибки, то можно
        # пройтись по списку и посчитать все несовпадения,
        # зафиксировав, например, в словарь, элементы, где несовпадения встретились
        assert rating[0] == get_ivi_app_rating_on_google_play(browser), (
                f'В элементе {rating[1]} отображаемая оценка не соответствует актуальной в Google Play')


def test_wikipedia_has_link_to_ivi(browser: webdriver) -> Optional[None]:
    '''Функция открывает сайт google.com, ищет в нём ivi,
    затем на первых 5 страницах поисковой выдачи находит ссылки на wikipedia,
    переходит по первой найденной ссылке и убеждается, что на ней есть ссылка на ivi.ru '''

    search_ivi_in_google(browser)
    # здесь специально ищу только по содержанию "wikipedia" в ссылке,
    # а не по прямой ссылке на страницу ivi на Википедии
    # чтобы, во-первых, найти нерелевантные ссылки (те, где нет ivi.ru)
    # во-вторых, чтобы ссылку ниже получить, как сказано в задании,
    # а то нелепо сначала по этой ссылке искать, а потом её же
    # зачем-то из href вытягивать
    wikipedia_links = get_elements_from_several_pages(
        browser, 5, '//a[contains(@href, "wikipedia")]', get_link_from_element)

    assert len(wikipedia_links) > 0, (
        'На 5 первых страницах google не найдено ни одной ссылки на wikipedia'
    )

    # по условию задания надо проверить только одну ссылку почему-то,
    # поэтому выцепляю первый элемент, иначе прошлась бы циклом просто,
    # как в предыдущем тесте
    browser.get(wikipedia_links[0])
    wait_for_page_load(browser)
    # здесь использую find_elements, чтобы не поднимать эксепшенов на ненайденный элемент
    link_to_ivi = browser.find_elements(By.XPATH, '//a[contains(@href, "ivi.ru")]')

    assert link_to_ivi != [], (
        f'На странице {wikipedia_links[0]} нет ссылки на ivi.ru.'
    )
