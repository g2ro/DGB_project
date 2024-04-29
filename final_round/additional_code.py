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

#MAIN_KEYWORD테이블에서 MAIN_K 찾기
def select_main():
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    cs = conn.cursor()
    select_main_keyword= 'select MAIN_K from MAIN_KEYWORD'
    cs.execute(select_main_keyword)
    
    main_keyword = cs.fetchall()
    cs.close()
    conn.close()
    return main_keyword

sub_k_list = ['사과','바나나','당근']

def insert_sub_keyword(main_k = str, sub_k_list = list):
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    print('DB connect 성공!!')
    
    cs = conn.cursor()
    
    main_k = main_k
    sub_list = sub_k_list
    
    insert_sub_keyword = 'INSERT INTO SUB_KEYWORD (MAIN_K, SUB_K) VALUES(:1, :2)'
    for i in range(len(sub_list)):
        cs.execute(insert_sub_keyword,(main_k, sub_list[i]))
        print('서브 키워드 INSERT 성공!!')
    
    cs.close()
    conn.commit()
    conn.close()

def sub_select():
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    cs = conn.cursor()
    # select_sub = 'SELECT * FROM SUB_KEYWORD'
    select_com = "SELECT MAIN_K || ' ' || SUB_K FROM SUB_KEYWORD"
    cs.execute(select_com)
    SUB_MAIN_C = cs.fetchall()
    
    cs.close()
    conn.close()
    return SUB_MAIN_C

def cleansing_sentence(input_string):
    string_pattern = re.compile(r'[^ㄱ-힣 0-9 a-z A-Z]')
    cleansing_string = string_pattern.sub('', input_string)
    return cleansing_string

def get_sub_data():
    sub = sub_select()
    for i in range(len(sub)):
        keyword = sub[i][0]
        get_data_keyword(keyword)

 # DB 저장 함수(크롤링 추출 자료 INSET)
def sub_title_insert(KEYWORD, TITLE): 
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
#     print('')
#     print('DB connect 성공!!')
#     print('')

    cs = conn.cursor()
    
    sql = "INSERT INTO SUB_TITLE (MAINSUB_K, TITLE) VALUES (:1, :2)"

    cs.execute(sql, (KEYWORD, TITLE))
    cs.close()
    conn.commit()
    conn.close()

def get_sub_title():
    sub_df_list=[]
    sub = sub_select()
    for i in range(len(sub)):
        keyword = sub[i][0]
        sub_df_list.append(make_df(f"SELECT * FROM SUB_TITLE WHERE MAINSUB_K like '{keyword}'"))
    return sub_df_list

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

def msnc_df(df, msk=str,title=str):
    okt = Okt()
    df =df
    msk = msk
    title = title
    
    #열 추출
    ms = list(df[msk])
    arr = np.array(df[title])
    #okt 명사 분해
    temp = []
    for i in range(len(arr)):
        temp.append(okt.nouns(arr[i]))
    #ms와 noun 한 번 묶기
    fir = []
    for i in range(len(temp)):
        fir.append([ms[i],temp[i]])
    #리스트 풀어서 2차원 리스트로 만들기
    fin=[]
    for i in range(len(fir)):
        for j in range(len(fir[i][1])):
            dic = [fir[i][0],fir[i][1][j]]
            fin.append(dic)
    #데이터프레임으로
    msn_df = pd.DataFrame(fin,columns = ['ms','noun'])
    #중복값 제거
    dut_df = msn_df.drop_duplicates(['noun'])
    #명사 목록 생성
    n_l = list(dut_df['noun'])
    
    num=[]
    for i in range(len(n_l)):
        num.append(len(msn_df[msn_df['noun']==n_l[i]]))
    M_df = dut_df.assign(count = num)
    msnc_df = M_df.sort_values('count',ascending=False)
    return msnc_df                        

def msk_nc_insert(msk_nc_df):
    df = msk_nc_df
    MS = list(df['ms'])
    NOUN = list(df['noun'])
    COUNT = list(df['count'])
    MAIN_K = select_main()[0][0] 
    
    conn = cx_Oracle.connect(user='admin', password='Tongbrown@23', dsn='tongbrown_high')
    print('DB connect 성공!!')
    cs = conn.cursor()
    sql = "INSERT INTO SUB_NOUN_COUNT (MAINSUB_K, NOUN, COUNT) VALUES(:1, :2, :3)"
    
    for i in range(len(df)):
        cs.execute(sql, (MS[i], NOUN[i], COUNT[i]))
        
    print('INSERT 성공!!')
    cs.close()
    conn.commit()
    conn.close()

#중복 제거
def dupl_drop(df):
    df = df
    main_k = select_main()[0][0]
    drop = df[df['noun'] == main_k].index
    df.drop(drop, inplace = True)
    drop1 = df[df['noun'] == sub].index
    df.drop(drop1, inplace = True)
    return df   

#한번만 실행하면 됨.
# cx_Oracle.init_oracle_client(lib_dir=r"C:\instantclient-basic-windows.x64-21.9.0.0.0dbru\instantclient_21_9")#db연결

if __name__ == '__main__':
    #초기 세팅
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--start-maximized')#chrome 사이즈 지정
    driver = webdriver.Chrome(chrome_options=chrome_options)
    service = Service(ChromeDriverManager().install())
    
    db_delete_sub()
    main_k = select_main()[0][0]
    sub_k_list = ['위기','한국은행','부도']
    insert_sub_keyword(main_k = main_k, sub_k_list = sub_k_list)
    
    get_sub_data()
    
    sub_title_df_list = get_sub_title()
    msnc_df_list=[]
    for i in range(len(sub_title_df_list)):
        sub = sub_k_list[i]
        df = msnc_df(sub_title_df_list[i],msk = 'MAINSUB_K',title = 'TITLE')
        df = dupl_drop(df)
        msnc_df_list.append(df)
    
    for j in range(len(msnc_df_list)):
        print(msnc_df_list[j].head(20))
        msk_nc_insert(msnc_df_list[j])