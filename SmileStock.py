# -*- coding: utf-8 -*-

import os
import sys, json, requests, re
import datetime
import time
import random
import logging
import pandas as pd

from json import dumps as json_encode

from urllib.parse import urljoin
from urllib import parse

from bs4 import BeautifulSoup as BS

#from tqdm.notebook import tqdm

from mecab import MeCab

#import konlpy
#from konlpy.tag import Okt
#import nltk

# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.options import Options

# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
    
import yfinance as yf
import FinanceDataReader as fdr

#from dash import Dash
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px

import joblib

from flask import Flask, request, jsonify, Response
from flask import render_template
from flask import make_response, redirect
from flask_restx import Api, Resource, reqparse

from config import *
from db import *

app = Flask(__name__)


dash_app1 = Dash( __name__, server = app, url_base_pathname='/dash1/' )

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

# dash app with simple component - https://dash.plotly.com/dash-html-components
dash_app1.layout = html.Div([
    html.H1(children='Title of Dash App', style={'textAlign':'center'}),
    dcc.Dropdown(df.country.unique(), 'Canada', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)

def update_graph(value):
    dff = df[df.country==value]
    return px.line(dff, x='year', y='pop')



#model = joblib.load('/home/ubuntu/SmileStock/model/RandomForestClassifier_model_20240110.pkl')
#df_words = pd.read_csv( "/home/ubuntu/SmileStock/model/data_words.csv", index_col=0 )

# home ----------------------------------------------------------------------------------------------------------------
#@app.route("/", methods=['GET', 'POST'] )
@app.route('/')
@app.route('/index.html')
def home():
    return render_template( 'index.html' )


# 추가 부분
description = "사용법: /Stocks?startDate=2024-01-01&endDate=2024-01-02&interval=1h&exchange=거래소&symbol=종목번호"
api = Api( app, version='1.0', title='API - Stocks', description=description, doc="/API/Stocks")
stocks_api = api.namespace( '/', description='yFinance 주식정보 조회 API')

#var query = Server + "/Stocks" + "?startDate=" + startDate + 
#"&endDate=" + endDate + "&interval=" + interval + "&symbol=" + symbol

app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
stocks_parser = api.parser()
stocks_parser.add_argument('startDate', required=True, help='시작일')
stocks_parser.add_argument('endDate', required=True, help='종료일')
stocks_parser.add_argument('interval', required=True, help='간격')
stocks_parser.add_argument('exchange', required=True, help='거래소')
stocks_parser.add_argument('symbol', required=True, help='종목번호')


@api.route('/API/Stocks')
@api.expect(stocks_parser)
class Stocks_docs(Resource):
    def get(self):

        args = stocks_parser.parse_args()

        try:
            startDate = args['startDate']
            endDate = args['endDate']
            interval = args['interval']
            exchange = args['exchange']
            symbol = args['symbol']
        
        except KeyError:
            return {'result': 'ERROR_PARAMETER'}, 500

        stocks = getStocks( startDate, endDate, interval, exchange, symbol )
        
        result = {'result': 'ERROR_SUCCESS', 'value': stocks }
        #result = {'result': 'ERROR_SUCCESS', 'value': 0 }
        return result, 200


@app.route('/Stocks', methods=['GET'])
def stocks():

    startDate = datetime.datetime.strptime( request.args.get( 'startDate' ), '%Y-%m-%d' )
    endDate = datetime.datetime.strptime( request.args.get( 'endDate' ), '%Y-%m-%d' )
    interval = request.args.get( 'interval', '' )
    exchange = request.args.get( 'exchange', '' )
    symbol = request.args.get( 'symbol', '' )

    #print( type(startDate), type(endDate) )
    print( '/Stocks/', 'StartDate:', startDate, ", EndDate:", endDate, ", Exchange:", exchange, "Symbol:", symbol ) 
    # "/Stocks" + "?startDate=" + startDate + "&endDate=" + endDate + "&interval=" + interval + "&exchange=" + exchange + "&symbol=" + symbol

    stocks = getStocks( startDate, endDate, interval, exchange, symbol )

    return make_response( stocks.encode("utf-8"), 200 )


def getStocks( startDate, endDate, interval, exchange, symbol ):
    
    ticker = f'{symbol}.KS' if exchange == 'KRX' else symbol
    print( ticker )
    stock = yf.Ticker( ticker )
    df = stock.history( interval=interval, start=startDate, end=endDate )
    print(df)

    # 리턴할 데이터프레임 변경
    drop_list = [ 'Dividends', 'Stock Splits' ]
    df.drop( drop_list, axis=1, inplace=True )
    df['Date'] = df.index
    df.reset_index(drop=True, inplace=True)
    #df['Date'] = df['Date'].apply(lambda x : datetime.datetime.strftime(x,'%Y년-%m월-%d일 %H:%M:%S'))

    #df.reset_index(inplace=True, drop=False)

    print(df)
    print(df.info())

    r = df.to_json( orient="columns" )
    #print( "json:", r, r.encode("utf-8") )

    return r


@app.route('/Company/<act>', methods=['GET'])
def company( act ):

    exchange = request.args.get( 'exchange', '' )
    symbol = request.args.get( 'symbol', '' )

    print( '/Company/', act, "Exchange:", exchange, "Symbol:", symbol ) 
    # "/Company" + "?exchange=" + exchange + "&symbol=" + symbol

    if ( act == 'get' ):

        company = getData( TABLE_Symbol, 'company', getWhere( 'symbol', symbol ) )

        if ( company == None ):
            company_data = { 'company': '찾을 수 없는 종목코드입니다!' }
        else:
            company_data = { 'company': company[0] }

    else:

        updateCompany( exchange )

        company_data = { 'company': exchange + ' 자료를 업데이트하였습니다!' }

    r = pd.DataFrame( [company_data] ).to_json( orient="columns" )

    return make_response( r.encode("utf-8"), 200 )


def updateCompany( exchange ):
      
    df_company = fdr.StockListing( exchange )
    #df_company.reset_index(drop=True, inplace=True)
    #company = df_company.loc[ df_company['Code'] == symbol ]
    #print(company)

    if ( exchange == 'KRX' ):
        df_company.rename( columns={ 'Code': 'symbol', 'Name': 'company' }, inplace=True )
        # Drop KRX: {'Code', 'ISU_CD': 'KR7322190000', 'Name': '베른', 'Market': 'KONEX', 'Dept': '일반기업부', 'Close': '115', 'ChangeCode': '1', 'Changes': 10, 'ChagesRatio': 9.52, 'Open': 119, 'High': 119, 'Low': 90, 'Volume': 1902, 'Amount': 171234, 'Marcap': 1026397655, 'Stocks': 8925197, 'MarketId': 'KNX'}
        drop_list = [ 'ISU_CD', 'Market', 'Dept', 'Close', 'ChangeCode', 'Changes', 'ChagesRatio', 'Open', 'High', 'Low', 'Volume', 'Amount', 'Marcap', 'Stocks', 'MarketId' ]

    #elif ( exchange == 'NYSE' ):
    else:
        df_company.rename(columns={ 'Symbol': 'symbol', 'Name': 'company' }, inplace=True)
        #Drop NYSE: { Symbol, Name,	IndustryCode, Industry }
        drop_list = [ 'IndustryCode', 'Industry' ]

    df_company.drop( drop_list, axis=1, inplace=True )

    result = False

    # DB 저장
    for idx, row in df_company.iterrows():

        company_row = row.to_dict()
        print( "Update DB:", exchange, idx, company_row )

        result = insertData( TABLE_Symbol, company_row )

    return result


@app.route('/News', methods=['GET'])
def news():

    startDate = request.args.get( 'startDate', '' )
    endDate = request.args.get( 'endDate', '' )
    exchange = request.args.get( 'exchange', '' )
    symbol = request.args.get( 'symbol', '' )

    #print( type(startDate), type(endDate) )
    print( '/News/', 'StartDate:', startDate, ", EndDate:", endDate, ", Exchange:", exchange, "Symbol:", symbol ) 
    # "/News" + "?startDate=" + startDate + "&endDate=" + endDate + "&exchange=" + exchange + "&symbol=" + symbol

    company = getData( TABLE_Symbol, 'company', getWhere( 'symbol', symbol ) )

    if ( company == None ):

        message_data = { 'message': '찾을 수 없는 종목코드입니다!' }

        r = pd.DataFrame( [message_data] ).to_json( orient="columns" )
        r_code = 400
    
    else:

        company_data = { 'company': company[0] }

        df = getNewsArticles( startDate, endDate, symbol )

        r = df.to_json( orient="columns" )
        r_code = 200
    
    #print( "json:", r, r.encode("utf-8"), r_code )

    return make_response( r.encode("utf-8"), r_code )


def getNewsArticles( start, end, symbol ):

    startTime = time.time()

    startDate = datetime.datetime.strptime( start + ' 00:00', '%Y-%m-%d %H:%M' )
    endDate = datetime.datetime.strptime( end + ' 23:59', '%Y-%m-%d %H:%M' ) 

    naverStockNews = "https://finance.naver.com/item/news_news.naver?code={symbol}&page={page}"

    req_header_dict = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
    }

    # Initialize Rerurn Data
    title_list = []
    link_list = []
    press_list = []
    date_list = []
    
    articleCount = 0
    duplicationCount = 0
    errorCount = 0
    
    nPage = 0
    
    while ( nPage >= 0 ):
    
        print( '-'*60 )
        nPage += 1
        
        naverStockNews_url = naverStockNews.format( symbol=symbol, page=nPage )
        print( nPage, 'Page Symbol:', symbol, 'NaverStockNews:', naverStockNews_url )
        
        res = requests.get( naverStockNews_url, headers=req_header_dict )
        #print( res.status_code, res.ok )
        #print( type(res) )
        #print( '응답헤더', res.headers, '요청헤더', res.request.headers )
        #print(res.text)
        
        if res.ok:
            
            html = res.text
            soup = BS( html, 'html.parser' )
            #sh_list = soup.select("div._persist > div.section_headline > ul > li > div.sh_text")
            item_list = soup.select( "body > div.tb_cont._replaceNewsLink > table.type5 > tbody > tr" )
            #print( len(item_list) )
    
            for idx, item in enumerate( item_list ):
            #for idx, item in tqdm( enumerate( item_list ) ):
    
                #print( idx, item['class'] )
                
                if ( item.select_one( "table.type5" ) == None ):
        
                    #print( idx, '-'*60 )
                    #print( '-'*60 )
                    
                    article_title = item.a.get_text()
                    #print( "Title:", article_title  )
                    
                    parse_link = parse.parse_qs( parse.urlparse( item.a['href'] ).query )
                    #print( "parse:", parse_link['article_id'][0], parse_link['office_id'][0], parse_link['code'][0] )
                    article_link = "https://n.news.naver.com/mnews/article/{office_id}/{article_id}".format( office_id=parse_link['office_id'][0], article_id=parse_link['article_id'][0] )
                    #print( "Link:", article_link )
        
                    article_press = item.select_one(".info").get_text()
                    #print( "Press:", article_press )
                    
                    article_datetime = item.select_one(".date").get_text().strip()
                    article_date = datetime.datetime.strptime( article_datetime, "%Y.%m.%d %H:%M" ) #2024.03.07 21:02
                    #article_date = datetime.datetime.strptime( article_datetime, "%Y-%m-%d %H:%M:%S" ) #2024.03.07 21:02
                    isDate = ( article_date >= startDate and article_date <= endDate )
                    #print( "Date:", article_datetime, article_date, isDate )
    
                    if ( isDate ):
    
                        # 중복 검사
                        if article_link not in link_list:
    
                            articleCount += 1
                            print( '#', articleCount, article_link )
    
                            # Append DataFrame 
                            title_list.append( article_title )
                            link_list.append( article_link )
                            press_list.append( article_press )
                            date_list.append( article_date )
                        
                        else:
                            duplicationCount += 1
                    
                    elif ( article_date >= startDate ):
                        continue

                    else:
                        nPage = -1
                        break
    
    endTime = time.time()
    #print( f'Complete! [실행 시간: {int(endTime - startTime)} 초]' )
    print( '\nTotal Articles:', len( link_list ), 'Duplicated Counts:', duplicationCount, 'Error Count:', errorCount, f'( Running Time: {int(endTime - startTime)} sec )' )
    
    result = {  'title'         : title_list,
                'link'          : link_list,
                'press'         : press_list,
                'date'          : date_list
    }
    
    # Make DataFrame
    df = pd.DataFrame( result )
    
    df["title"] = df["title"].str.replace( pat=r'[^\w]', repl=r' ', regex=True )

    return df


@app.route('/Classification', methods=['POST'])
def classification():

    article = request.form.get( 'article', '' )
    #print( 'article:', article )

    r = getClassfication( article )

    return make_response( r.encode("utf-8"), 200 )


def getClassfication( article ):

    print( "Article:", article )

    #print( "Location:", os.getcwd() )

    #okt = Okt()
    mecab = MeCab()

    #raw = okt.pos( article, norm=True, stem=True )
    raw = mecab.pos( article )
    print( "Pos:", raw )
    
    words = []
    for word, pos in raw:
        #if pos in ["Noun", "Verb", "Adjective", "Adverb"]:  #okt
        if pos in ["NNG", "VV", "VA", "AD"]:   #mecab
            words.append(word)
    print( "Words:", words )

    vc = pd.Series(words).value_counts()
    print( "Vc:", vc )

    df_words = pd.read_csv( "/home/ubuntu/SmileStock/model/data_words.csv", index_col=0 )
    print( "DataWords:", df_words )

    temp = pd.DataFrame( columns=df_words.columns )

    for word in vc.index:
        count = vc.loc[word]
        if word in df_words.columns:
            temp.loc[0, word] = count

    temp.fillna( 0, inplace=True )
    #print( "Temp:", temp )

    section = { 0: "정치", 1: "경제", 2: "사회", 3: "생활/문화", 4: "세계", 5: "IT/과학" }

    model = joblib.load('/home/ubuntu/SmileStock/model/RandomForestClassifier_model_20240110.pkl')
    print( "Model loaded!" )

    predict = model.predict( temp )

    predictResult = "이 기사는 '" + section[ predict[0] ] + "' 뉴스입니다!"
    print( predictResult )
    #predictResult = "서버 지연으로 아직 제공되지 않습니다."

    return predictResult


# ----------------------------------------------------------------------------------------------------------------------

if __name__=="__main__":

    createDB_SmileStock()

    #createTestTable()

    app.run(host='0.0.0.0', debug=True)
 
    print("Hello SmileStock!")