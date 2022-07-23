import requests
from bs4 import BeautifulSoup
import json
import re

URL = input('Введите ссылку на категорию: ').strip()
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36', 'accept': '*/*'}
URL = URL.replace('page=1&', '')


def get_html(url, params= None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_="product-card__wrapper")
    links = []
    for item in items:
        link = item.find('a', class_='product-card__main').get('href')
        links.append('https://www.wildberries.ru'+link)
    return links


def get_content(link, html):
    goods = []
    feedlist = []
    qa = []
    soup = BeautifulSoup(html, 'html.parser')
    try:
        rating = soup.find(itemprop="ratingValue").get("content")
    except AttributeError:
        rating = "не указан"
    price = soup.find(itemprop="price").get("content")
    link = link.replace('https://www.wildberries.ru/catalog/','').replace('/detail.aspx', '').replace('?targetUrl=GP', '')
    data = requests.get(f'https://wbx-content-v2.wbstatic.net/ru/{link}.json')
    data = json.loads(data.text)
    imt_id = data['imt_id']
    payload = {'imtId': imt_id, 'skip': 0, 'take': 30, 'order': "dateDesc"}
    feedback = requests.post('https://public-feedbacks.wildberries.ru/api/v1/feedbacks/site', json=payload, headers=HEADERS)
    feedback = json.loads(feedback.text)
    questions = requests.get(f'https://questions.wildberries.ru/api/v1/questions?imtId={imt_id}&skip=0&take=30')
    questions = json.loads(questions.text)
    try:
        for question in questions['questions']:
            qa.append({
                'Вопрос': question['text'],
                'Ответ': question['answer']['text']
            })
    except TypeError:
        pass
    for feed in feedback['feedbacks']:
        feedlist.append({
            'Отзыв': feed['text'],
            'Оценка' : feed['productValuation']
        })
    goods.append({
        'id': data['nm_id'],
        'Название': data['imt_name'],
        'Тип товара': data['subj_name'],
        'Категория': data['subj_root_name'],
        'Бренд': data['selling']['brand_name'],
        'Цена': price,
        'Рейтинг': rating,
        'Характеристики': data['options'],
        'Отзывы': feedlist,
        'Вопосы - ответы': qa

    })
    return goods


def get_pages(html):
    soup = BeautifulSoup(html, 'html.parser')
    count = soup.find('span', class_='goods-count').get_text(strip=True)
    count = [int(s) for s in re.findall(r'-?\d+\.?\d*', count)]
    count = int(''.join(map(str, count)))
    return int(count/100 + 1)


def main():
    html = get_html(URL)
    if html.status_code == 200:
        links = []
        goods = []
        pages_count = get_pages(html.text)
        for page in range(1, pages_count + 1):
            html = get_html(URL, params={"page": page})
            links.extend(get_links(html.text))
        print(f'Получено {len(links)} товаров')
        i = 0
        for link in links:
            i += 1
            print(f'Парсинг {i} из {len(links)}')
            html = get_html(link)
            goods.extend(get_content(link, html.text))
        with open('date_f.json', 'w', encoding='utf8') as write_file:
            json.dump(goods, write_file, ensure_ascii=False)


if __name__ == '__main__':
    main()
