import os.path

import requests
from dotenv import load_dotenv
from progress.bar import IncrementalBar
from terminaltables import AsciiTable


def print_statistics(statistics, languages):

    table_data = [['Язык программирования',
                   'Вакансий найдено',
                   'Вакансий обработано',
                   'Средняя зарплата']]
    for language in languages:
        table_data.append([language,
                           statistics[language]['vacancies_found'],
                           statistics[language]['vacancies_processed'],
                           statistics[language]['average_salary']])

    table = AsciiTable(table_data)
    print(table.table)


def predict_salary(salary_from, salary_to):
    salary = None
    if salary_from and salary_to:
        salary = int((salary_from + salary_to) / 2)
    elif salary_from:
        salary = int(salary_from * 1.2)
    elif salary_to:
        salary = int(salary_to * 0.8)

    return salary


def predict_rub_salary_hh(vacanci):
    salary_info = vacanci['salary']
    currency = ['RUR', 'RUB']
    if salary_info:
        if salary_info['currency'] in currency:
            salary_from = salary_info['from']
            salary_to = salary_info['to']
            salary = predict_salary(salary_from, salary_to)
            return salary


def predict_rub_salary_sj(vacanci):
    salary_from = vacanci['payment_from']
    salary_to = vacanci['payment_to']
    if vacanci['currency'] == 'rub':
        salary = predict_salary(salary_from, salary_to)
    return salary


def fetch_hh_salary(pages_number, language):
    url = 'https://api.hh.ru/vacancies'
    page = 0
    salary = 0
    vacancies_processed = 0
    params = {'text': f'программист {language}',
              'page': page,
              'area': 1,
              'period': 30}
    bar = IncrementalBar(f'{language} head hunter progress', max=pages_number)
    while page < pages_number:

        response = requests.get(url, params=params)
        response.raise_for_status()
        page += 1
        bar.next()
        data = response.json()
        vacancies_found = data['found']
        vacancies = data['items']
        for vacanci in vacancies:
            predicted_salary = predict_rub_salary_hh(vacanci)
            if predicted_salary:
                salary += predicted_salary
                vacancies_processed += 1
    try:
        average_salary = int(salary / vacancies_processed)
    except ZeroDivisionError:
        pass

    bar.finish()
    return vacancies_found, vacancies_processed, average_salary


def fetch_sj_salary(pages_number, language):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    page = 0
    salary = 0
    vacancies_processed = 0
    vacancies_found = 0
    params = {'keyword': f'Программист, Разработка, {language}', 'town': 4}
    headers = {'X-Api-App-Id': super_job_token}
    bar = IncrementalBar(f'{language} super job progress', max=pages_number)

    while page < pages_number:

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        page += 1
        bar.next()
        data = response.json()
        vacancies = data['objects']
        vacancies_found += len(vacancies)
        for vacanci in vacancies:
            predicted_salary = predict_rub_salary_sj(vacanci)
            if predicted_salary:
                salary += predicted_salary
                vacancies_processed += 1
            try:
                average_salary = int(salary / vacancies_processed)
            except ZeroDivisionError:
                pass

    bar.finish()
    return vacancies_found, vacancies_processed, average_salary


if __name__ == '__main__':
    hh_salaries = {}
    sj_salaries = {}
    load_dotenv()
    super_job_token = os.getenv('SUPER_JOB_TOKEN')
    pages_number = 100
    languages = ['Go',
                 'C#',
                 'C++',
                 'PHP',
                 'Ruby',
                 'Python',
                 'Java',
                 'JavaScript']

    for language in languages:
        hh_found, hh_processed, hh_salary = fetch_hh_salary(pages_number, language)
        sj_found, sj_processed, sj_salary = fetch_sj_salary(pages_number, language)

        hh_salaries[language] = {'vacancies_found': hh_found,
                                 'vacancies_processed': hh_processed,
                                 'average_salary': hh_salary}
        sj_salaries[language] = {'vacancies_found': sj_found,
                                 'vacancies_processed': sj_processed,
                                 'average_salary': sj_salary}

    print_statistics(hh_salaries, languages)
    print_statistics(sj_salaries, languages)
