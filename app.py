import pandas as pd
import requests
from bs4 import BeautifulSoup
import math
import streamlit as st
from concurrent.futures import ThreadPoolExecutor

headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"}
session = requests.Session()

def get_jobs(search):
    page = session.get(f"https://ph.joblum.com/jobs-{search.replace(' ','+')}?p=1", headers=headers)
    soup = BeautifulSoup(page.content, 'lxml')
    total_jobs = int(soup.find_all('p', class_="pull-left no-of-jobs")[0].get_text().split()[-2])
    no_pages = math.ceil(int(total_jobs)/10)

    return no_pages, total_jobs

def scrape(no_pages, search):
    urls = []
    for i in range(1,no_pages+1):
        urls.append(f"https://ph.joblum.com/jobs-{search.replace(' ','+')}?p={i}")

    def make_request(url):
        response = session.get(url, headers=headers)
        return response

    with ThreadPoolExecutor(max_workers=30) as executor:
        page = list(executor.map(make_request, urls))

    soup = []
    post = []
    for i in range(len(page)):
        soup.append(BeautifulSoup(page[i].content, 'lxml'))
        post.append(soup[i].find_all('div', class_='col-md-10 col-xs-12 item-details'))

    test = []
    for j in range(len(post)):
        for i in range(len(post[j])):
            temp = []
            temp.append(post[j][i].find_all('a')[1]['title'])

            try:
                temp.append(post[j][i].find_all('div', class_='new-time')[0].find('div', string=lambda text: 'PHP' in text).text.strip())
            except:
                temp.append('unknown')

            try:
                temp.append(post[j][i].find_all('span', class_='company-name')[0].find('span').text.strip())
            except:
                temp.append('unknown')
                
            temp.append(post[j][i].find_all('span', class_='location')[0].find('span').text.strip())
            temp.append(str('https://ph.joblum.com') + post[j][i].find(href=True)['href'])
            test.append(temp)

    df = pd.DataFrame(test, columns=['title', 'salary', 'company', 'location', 'link'])
    df = pd.DataFrame(test, columns=['title', 'salary', 'company', 'location', 'link'])
    df = df[df['salary'] != 'unknown'].reset_index(drop=True)
    df['salary_low'] = df['salary'].str.split(' ', expand=True).drop(0, axis=1)[1]
    df['salary_high'] = df['salary'].str.split(' ', expand=True).drop(0, axis=1)[3]
    df['salary_low'] = df['salary_low'].str.replace(',','').astype('float')
    df['salary_high'] = df['salary_high'].str.replace(',','').astype('float')
    df.loc[df[df['salary_high'].isna()].index, 'salary_high'] = df[df['salary_high'].isna()]['salary_low']
    df = df.drop('salary', axis=1)
    df = df[['title', 'salary_low', 'salary_high', 'company', 'location', 'link']]

    return df

def main():
    st.title('Joblum Scraper')
    job_name = st.text_input('Enter job title')
    if st.button("Scrape jobs"):
        #start = time.time()
        search = job_name
        no_pages, total_jobs = get_jobs(search)
        df = scrape(no_pages, search)
        st.dataframe(df)
        #st.write(time.time()-start)
        csv = df.to_csv(index=False)

        st.download_button(
        "Download CSV",
        csv,
        "file.csv",
        "text/csv",
        key='download-csv'
        )

if __name__ == "__main__":
    main()