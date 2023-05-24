import json
import os
import pandas as pd
import sys
import time
from pprint import pprint

import requests
from bs4 import BeautifulSoup

results = []
site_url = 'https://www.entrepreneur.com/'
table_page_template = 'https://www.entrepreneur.com/franchises/500/2021/{page}'
with open('columns_names', 'r') as file:
    content = file.readlines()
    all_attrs = [elem.strip('\n') for elem in content]

chart_selector = '#widgetChart'


def ensure_left_bracket(filename):
    with open(filename, 'r+', encoding='utf-8') as file:
        first_line = file.readline()
        if not first_line or first_line[0] != '[':
            file.seek(0, 0)
            file.write('[' + first_line)


def ensure_right_bracket(filename):
    with open(filename, 'r+', encoding='utf-8') as file:
        file.seek(0, os.SEEK_END)
        file.seek(file.tell() - 2, os.SEEK_SET)
        if file.read(1) != ']':
            file.seek(file.tell() - 1, os.SEEK_SET)
            file.write(']')


def remove_right_bracket(filename):
    with open(filename, 'r+', encoding='utf-8') as file:
        file.seek(0, os.SEEK_END)
        file.seek(file.tell() - 2, os.SEEK_SET)
        if file.read(1) == ']':
            file.seek(file.tell() - 1, os.SEEK_SET)
            file.write(',\n')
        # print(file.read())


def json_to_excel(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
        df = pd.DataFrame(data)
        df.drop(columns='Data per year', inplace=True)
        df.to_excel('results.xlsx', index=False)


def main():
    try:
        with open('results(copy).json', 'r', encoding='utf-8'):
            pass
    except FileNotFoundError:
        with open('results(copy).json', 'w', encoding='utf-8'):
            pass
    with open('results(copy).json', 'r+', encoding='utf-8') as file:
        lines_count = len(file.readlines())
        page_index = lines_count // 50
        link_count = lines_count % 50
        # print(lines_count, page_index, link_count)
    ensure_left_bracket('results(copy).json')
    if lines_count > 0:
        remove_right_bracket('results(copy).json')
        print(f'{lines_count} links has been already preprocessed. '
              f'{"Data is already fully scraped" if lines_count>=500 else "Starting from {}".format(lines_count+1)}')
    time.sleep(3)
    links_overall = lines_count

    last_page_num = 10
    for i in range(page_index + 1, last_page_num + 1):
        try:
            response = requests.get(table_page_template.format(page=i))
            bs_links_page = BeautifulSoup(response.text, 'lxml')
            links = bs_links_page.select('.block.w-full.col-span-2')
            if link_count:
                links = links[link_count:]
            time.sleep(2)

            for link in links:
                temp = dict.fromkeys(all_attrs, '')
                franchise_html = requests.get(site_url + link['href'])
                time.sleep(2)
                bs_franchise = BeautifulSoup(franchise_html.text, 'lxml')
                row_tags = bs_franchise.find_all('dt')
                for row in row_tags:
                    row_name = row.get_text(strip=True)
                    try:
                        if row_name in ('Marketing Support', 'Ongoing Support'):
                            buffer = row.find_next('dd').get_text()
                            buffer = buffer.strip().split('\n' * 6)
                            buffer = ', '.join(buffer)
                            temp[row_name] = buffer
                        elif row_name.find('Units as of 20') != -1:
                            temp[row_name] = row.find_next('span').get_text(strip=True)
                            temp['Growth'] = row.find_next('span', {'class': True}).get_text(strip=True)
                        elif row_name == '2021 Franchise 500 Rank':
                            temp[row_name] = row.find_next('span').find_next(string=True).get_text(strip=True)
                            print(temp[row_name])
                            temp['Ranked last year'] = row.find_next('span', {'class': True}).get_text(strip=True)
                        else:
                            temp[row_name] = row.find_next('dd').get_text(strip=True)
                        chart_data = bs_franchise.select_one(chart_selector)
                        actual_data = json.loads(chart_data['data-chartdata'])
                        temp['Data per year'] = actual_data
                    except AttributeError:
                        # print(dir(err))
                        print('Attribute error occurred, closing program.')
                        ensure_right_bracket('results(copy).json')
                        sys.exit(1)
                results.append(temp)
                pprint(temp)
                link_count += 1
                links_overall = (i - 1) * 50 + link_count
                print(f'{links_overall}/{500}')
                with open('results(copy).json', 'a+') as res:
                    json.dump(temp, res)
                    res.write(',\n')
            link_count = 0

        except KeyboardInterrupt:
            ensure_right_bracket('results(copy).json')
            print('Error occurred: interrupted by keyboard.')
            print('Preserving data. Closing program')
            sys.exit()
    ensure_right_bracket('results(copy).json')
    if links_overall >= 500:
        json_to_excel('results(copy).json')
        print('Excel file has been successfully created!')


if __name__ == '__main__':
    main()
