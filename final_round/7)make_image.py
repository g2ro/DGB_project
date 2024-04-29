from selenium import webdriver
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import quote
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import time
import random
import cx_Oracle
import re
from selenium.webdriver.chrome.service import Service
from openpyxl import Workbook
from selenium.common.exceptions import ElementNotInteractableException ## 추가됨
from selenium.common.exceptions import NoSuchElementException ## 추가됨
import sys ## 추가됨
import pandas as pd
import numpy as np
import os
from konlpy.tag import Okt
from wordcloud import WordCloud 
import matplotlib.pyplot as plt
from PIL import *

#메인 키워드 저장
def insert_main(keyword):
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    cs = conn.cursor()
    sql_insert = 'INSERT INTO MAIN_KEYWORD (MAIN_K) VALUES (:1)'

    cs.execute(sql_insert, (keyword,))
    
    cs.close()
    conn.commit()
    conn.close()

#무한 스크롤
def scroll():
    try:       
        # 페이지 내 스크롤 높이 받아오기
        last_page_height = driver.execute_script("return document.documentElement.scrollHeight")
        while True:
            # 임의의 페이지 로딩 시간 설정
            # PC환경에 따라 로딩시간 최적화를 통해 scraping 시간 단축 가능
            pause_time = random.uniform(1, 2)
            # 페이지 최하단까지 스크롤
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            # 페이지 로딩 대기
            time.sleep(pause_time)
            # 무한 스크롤 동작을 위해 살짝 위로 스크롤(i.e., 페이지를 위로 올렸다가 내리는 제스쳐)
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight-50)")
            time.sleep(pause_time)
            # 페이지 내 스크롤 높이 새롭게 받아오기
            new_page_height = driver.execute_script("return document.documentElement.scrollHeight")
            # 스크롤을 완료한 경우(더이상 페이지 높이 변화가 없는 경우)
            if new_page_height == last_page_height:
                print("스크롤 완료")
                break
                
            # 스크롤 완료하지 않은 경우, 최하단까지 스크롤
            else:
                last_page_height = new_page_height
            
    except Exception as e:
        print("에러 발생: ", e)


#문장 정리
def cleansing_sentence(input_string):
    string_pattern = re.compile(r'[^ㄱ-힣 0-9 a-z A-Z]')
    cleansing_string = string_pattern.sub('', input_string)
    return cleansing_string

#테이블에 삽입
def db_insert(title,link):
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    print('DB connect 성공!!')
    
    cs = conn.cursor()
    
    sql = "INSERT INTO MAIN_TITLE (MAIN_K,TITLE) VALUES (:1, :2)"

    cs.execute(sql, (title,link))
    
    print("INSERT 완료")
    cs.close()
    conn.commit()
    conn.close()

#sql문으로 db에서 값 가져오기
def make_df(sql):
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    cs = conn.cursor()
    sql = sql
    cs.execute(sql)
    row = cs.fetchall()
    colname = cs.description
    col = []
    for i in colname:
        col.append(i[0])
    df =  pd.DataFrame(row,columns = col)
    return df

# okt를 통한 명사 분석 = 키워드 추출
def keyword_okt_noun(column):
    okt = Okt()
    arr = np.array(column)
    temp = []
    for i in range(len(arr)):
        temp.append(okt.nouns(arr[i]))
    noun = sum(temp,[])
    df = pd.DataFrame({'Noun':noun})
    noun_set = set(noun)
    noun_kind = list(noun_set)
    num=[]
    j=0
    for i in range(len(noun_kind)):
        num.append(len(df[df['Noun']==noun_kind[j]]))
        j=j+1
    #데이터프레임 생성 및 정렬
    df1 = pd.DataFrame({'Noun':noun_kind,'count':num})
    df1s = df1.sort_values('count',ascending=False)
    return df1s

def mk_nc_insert(mk_nc_df):
    df = mk_nc_df
    NOUN = list(df['Noun'])
    COUNT = list(df['count'])
    MAIN_K = select_main()[0][0] 
    
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    print('DB connect 성공!!')
    cs = conn.cursor()
    sql = "INSERT INTO MAIN_NOUN_COUNT (MAIN_K, NOUN, COUNT) VALUES(:1, :2, :3)"
    
    for i in range(len(df)):
        cs.execute(sql, (MAIN_K, NOUN[i], COUNT[i]))
        
    print('INSERT 성공!!')
    cs.close()
    conn.commit()
    conn.close()

#메인 키워드 가져오기.
def select_main():
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    cs = conn.cursor()
    select_main_keyword= 'select MAIN_K from MAIN_KEYWORD'
    cs.execute(select_main_keyword)
    
    main_keyword = cs.fetchall()
    cs.close()
    conn.close()
    return main_keyword

def word_cloud(str):
    
    df = str
    
    MAIN_K = select_main()[0][0]
    
    cand_mask=np.array(Image.open('circle.jpg'))

    nword = list(df['Noun'])

    ncount = list(df['count'])

    words = dict(zip(nword,ncount))

    wordcloud = WordCloud(
        font_path = 'malgun.ttf', # 한글 글씨체 설정
        background_color='white', # 배경색은 흰색으로 
        colormap='Blues', # 글씨색은 빨간색으로
        mask=cand_mask, # 워드클라우드 모양 설정
    ).generate_from_frequencies(words)

    plt.figure(figsize=(5,5))
    plt.imshow(wordcloud,interpolation='bilinear')
    plt.axis('off')
    
    plt.savefig(f"C:/Users/effor/바탕 화면/{MAIN_K}.png")

#메인 키워드는 서비 키워드에서 제외.
def dupl_drop(df):
    df = df
    MAIN_K = select_main()[0][0]
    drop = df[df['Noun']==MAIN_K].index
    df.drop(drop, inplace = True)
    return df   
    

# cx_Oracle.init_oracle_client(lib_dir=r"C:\instantclient-basic-windows.x64-21.9.0.0.0dbru\instantclient_21_9")

if __name__ == '__main__':
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--start-maximized')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    service = Service(ChromeDriverManager().install())
    
    MK_DF = make_df('SELECT * FROM MAIN_TITLE WHERE TITLE IS NOT NULL')
    MK_NC = keyword_okt_noun(MK_DF['TITLE'])
    MK_NC1 = dupl_drop(MK_NC)
    print(MK_NC1)
    mk_nc_insert(MK_NC1)
    
#     word_cloud(MK_NC1)