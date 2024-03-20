# -*- coding: utf-8 -*-

import os
import sys

import timeit
import datetime
import json
import pandas as pd

import mysql.connector as mdb

from config import *


def createTestTable():

    df = pd.DataFrame( data=[['Stephen', '데이터 과학자'], ['Jane', '데이터 분석가']], columns=['name', 'job'])

    result = False

    # DB 저장
    for idx, row in df.iterrows():

        test_data = row.to_dict()
        print( "DB:", idx, row['name'], type(row), type(test_data), test_data )

        # test_data = {   'name'       : row['name'],
        #                 'job'        : row['job']
        # }
        
        result = insertData( TABLE_Test, test_data )

    return result



def createDB_SmileStock():

    print( "* DB", DB_Name, Host_Name, Port_No, User_Name, Pass_Word, DB_Name, Char_Set )

    result = False

    # Open database connection
    db = mdb.connect(
        host = Host_Name,           # MySQL 서버 호스트
        user = User_Name,           # MySQL 사용자 이름
        password = Pass_Word,       # MySQL 암호
        database = DB_Name,          # 연결할 데이터베이스
        port = 3306
    )

    print( 'db:', db )

    try:

        cursor = db.cursor()

        # execute SQL query using execute() method.
        cursor.execute( "SELECT VERSION()" )
        print( "Database version : %s " % cursor.fetchone() )

        # NaverNews Table
        sql = """
            (
            newsDate datetime,
            category varchar(30) default '',
            press varchar(50) default '',
            title varchar(100) default '',
            document text,
            documentHead text,
            link varchar(100) default '',
            summary text,
            primary key( link )
            )
            """
        #createTable( TABLE_News, DB_Name, sql, cursor )

        # Member Table
        sql = """
            (
            member_id int auto_increment,
            member_email varchar(50) default '',
            primary key( member_id )
            )
            """
        createTable( TABLE_Member, DB_Name, sql, cursor )

        # MemberSymbol Table
        sql = """
            (
            member_id int,
            symbol varchar(10),
            slot int,
            primary key( member_id )
            )
            """
        createTable( TABLE_MemberSymbol, DB_Name, sql, cursor )

        # Symbol Table
        sql = """
            (
            symbol varchar(10),
            company varchar(100),
            primary key( symbol )
            )
            """
        createTable( TABLE_Symbol, DB_Name, sql, cursor )

        # Articles Table
        sql = """
            (
            symbol varchar(10),
            date datetime,
            link varchar(100),
            emotion tinyint
            )
            """
        createTable( TABLE_Articles, DB_Name, sql, cursor )

        # Prediction Table
        sql = """
            (
            symbol varchar(10),
            date datetime,
            prediction tinyint,
            primary key( symbol, date )
            )
            """
        createTable( TABLE_Prediction, DB_Name, sql, cursor )

        # Analysis Table
        sql = """
            (
            symbol varchar(10),
            date datetime,
            analysis tinyint,
            primary key( symbol, date )
            )
            """
        createTable( TABLE_Analysis, DB_Name, sql, cursor )

        # PairTrading Table
        sql = """
            (
            member_id int,
            site varchar(10),
            symbol1 varchar(10),
            symbol2 varchar(10),
            startDate datetime,
            endDate datetime,
            algorithm int,
            primary key( member_id )
            )
            """
        createTable( TABLE_PairTrading, DB_Name, sql, cursor )


        # to_sql Test Table
        sql = """
            (
            symbol varchar(10),
            company varchar(50),
            primary key( symbol )
            )
            """
        createTable( TABLE_Test, DB_Name, sql, cursor )


        # 연결 및 커서 닫기
        cursor.close()
        db.close()

        result = True

    except mdb.Error as e:
        #except mysql.connector.errors.ProgrammingError as err:
        db.rollback()
        print( "Error: %d, %s" % ( e.args[0], e.args[1] ) )
        #sys.exit(1)

    except FileNotFoundError as e:
        print( 'Error occured: ', e )

    finally:
        print('finally close')
        if db:
            db.close()

    return result


def createTable( tableName, dbName, sql, cursor ):
# Table Shmema를 확인하고 없으면 테이블을 새로 생성한다.

    schemaSql = "Select 1 From Information_Schema.tables Where Table_Name='" + tableName + "' and Table_Schema='" + dbName + "'"

    cursor.execute( schemaSql )

    if ( cursor.fetchone() == None ):

        # SQL 쿼리 실행
        cursor.execute( 'CREATE TABLE ' + tableName + ' ' + sql )
        print( 'Create Table:', tableName, 'on DB:', dbName )

        # 결과 가져오기
        results = cursor.fetchall()


def insertData( table, tableValue, dbName=DB_Name, InsertMode="INSERT" ):
# Table에 새로운 데이타{ 'field': value }를 추가한다.
    #print( '[insertData] table:', table, '/tableValue:', tableValue )

    result = False

    try:
        # Open database connection
        db = mdb.connect(
            host = Host_Name,           # MySQL 서버 호스트
            user = User_Name,           # MySQL 사용자 이름
            password = Pass_Word,       # MySQL 암호
            database = dbName           # 연결할 데이터베이스
        )

        #cursor = db.cursor( mdb.cursors.DictCursor )
        cursor = db.cursor()

        fields = ''
        values = ''
        count = 0

        for key, value in tableValue.items():

            fields += key
            quotation = getQuotation( value )
            values += quotation + str( value ) + quotation

            count += 1
            if count < len( tableValue ):
                fields += ','
                values += ','

        #print( 'fields:', fields, '/values:', values )

        sql = InsertMode + " INTO " + table + " ( " + fields + " ) VALUES ( " + values + " )"
        #print( '[insert/ReplaceData] sql:', sql )

        #print( 'sql.encode():', sql.encode() )
        cursor.execute( sql.encode() )
        db.commit()

        result = True

    except mdb.Error as e:
        # except mysql.connector.errors.ProgrammingError as err:
        print( 'Insert/Replace Error: %d, %s' % ( e.args[0], e.args[1] ) )
        db.rollback()


    except FileNotFoundError as e:
        print( 'Error occured in insert: ', e )
        db.rollback()


    finally:
        # print('finally close')
        if db:
            db.close()

    return result


def replaceData( table, tableValue, dbName=DB_Name ):
# Table에 새로운 데이타{ 'field': value }를 대치한다.
    #print( '[replaceData] table:', table, '/tableValue:', tableValue )

    return insertData( table, tableValue, dbName, InsertMode="REPLACE" )


def updateData( table, where, tableValue, dbName=DB_Name ):
# Table로부터 조건(where)에 맞는 데이타를 업데이트한다.
    #print( '[updateData] table:', table, '/where:', where, '/tableValue:', tableValue )

    result = False

    try:
        # Open database connection
        db = mdb.connect(
            host = Host_Name,           # MySQL 서버 호스트
            user = User_Name,           # MySQL 사용자 이름
            password = Pass_Word,       # MySQL 암호
            database = dbName           # 연결할 데이터베이스
        )

        #cursor = db.cursor( mdb.cursors.DictCursor )
        cursor = db.cursor()

        setValue = ''
        count = 0

        for field, value in tableValue.items():
            count += 1
            setValue += field + "= '" + str(value) + "'" + ( ',' if count < len(tableValue) else '' )

        #print( '[updateData] setValue:', setValue )

        sql = 'UPDATE ' + table + ' SET ' + setValue + ' WHERE ' + where
        #print( '[updateData] sql:', sql )

        #print( 'sql.encode():', sql.encode() )
        cursor.execute( sql.encode() )
        db.commit()

        result = True

    except mdb.Error as e:
        # except mysql.connector.errors.ProgrammingError as err:
        db.rollback()
        print( 'Update Error: %d, %s' % ( e.args[0], e.args[1] ) )
        #sys.exit(1)

    except FileNotFoundError as e:
        print( 'Error occured in update: ', e )

    finally:
        #print('finally close')
        if db:
            db.close()

    return result


def deleteData( table, where, dbName=DB_Name ):
# Table로부터 조건(where)에 맞는 데이타를 삭제한다.
    #print('[deleteData] table:', table, '/where:', where )

    result = False

    try:
        # Open database connection
        db = mdb.connect(
            host = Host_Name,           # MySQL 서버 호스트
            user = User_Name,           # MySQL 사용자 이름
            password = Pass_Word,       # MySQL 암호
            database = dbName           # 연결할 데이터베이스
        )

        #cursor = db.cursor( mdb.cursors.DictCursor )
        cursor = db.cursor()

        sql = 'DELETE FROM ' + table + ' WHERE ' + where
        #print( '[deleteData] sql:', sql )

        # print( 'sql.encode():', sql.encode() )
        cursor.execute( sql.encode() )
        db.commit()

        result = True

    except mdb.Error as e:
        # except mysql.connector.errors.ProgrammingError as err:
        db.rollback()
        print( 'Delete Error: %d, %s' % ( e.args[0], e.args[1] ) )
        #sys.exit(1)

    except FileNotFoundError as e:
        print( 'Error occured in delete: ', e )

    finally:
        # print('finally close')
        if db:
            db.close()

    return result


def getDataList( table, fields, where=None, many=MANY_ALL, order=None ):
#Table로부터 조건에 맞는 리스트를 가져온다

    dataList = []

    data = getData( table, fields=fields, where=where, many=many, order=order )
    if ( data != None ):

        fieldsName = fields.replace( 'DISTINCT', '' ).strip()
        #print( 'getDataList:', table, fields, fieldsName, data, type( data ), len( data ) )

        if ( type( data ) == tuple ):
            for d in data:
                dataList.append( d.get( fieldsName ) )
        elif ( type( data ) == dict ):
            dataList.append( data.get( fieldsName ) )

    print( 'getDataList data:', data, 'dataList:', dataList )

    return dataList


def getData( table, fields='*', where=None, many=MANY_1, order=None, dbName=DB_Name ):
# Table로부터 조건(where)에 맞는 데이타배열을 가져온다.
    #print( '[getData] table:', table, '/where:', where, '/many:', many )

    try:
        # Open database connection
        db = mdb.connect(
            host = Host_Name,           # MySQL 서버 호스트
            user = User_Name,           # MySQL 사용자 이름
            password = Pass_Word,       # MySQL 암호
            database = dbName           # 연결할 데이터베이스
        )

        #cursor = db.cursor( mdb.cursors.DictCursor )
        cursor = db.cursor()

        #sql = "SELECT * FROM " + table + " WHERE " + getWhereSQL( where )
        sql = "SELECT " + fields + " FROM " + table + ( " WHERE " + where if ( where != None ) else '' ) + ( " ORDER BY " + order if ( order != None ) else '' )
        #print( 'getData:', sql )

        cursor.execute( sql )

        if ( many == MANY_1 ):
            #rows = cursor.fetchone()
            rows = cursor.fetchmany( many )
        else:
            rows = cursor.fetchall()

        rowCount = len(rows)

        #print( '[getData] sql:', sql+'\n', '/rows:', rows, '/len:', rowCount, '/type:', type(rows) )

        if ( rowCount == 0 ):
            data = None

        else:
            #data = getTableList( cursor.description, 'id', rows )
            getDeleteKeyInRows( rows, 'id' )

            if ( len(rows) == many == 1 ):
                data = rows[0]
            else:
                data = rows


    except mdb.Error as e:
        # except mysql.connector.errors.ProgrammingError as err:
        print( 'GetData Error: %d, %s' % ( e.args[0], e.args[1] ) )
        #db.rollback()
        data = None
        #sys.exit(1)

    except FileNotFoundError as e:
        print( 'Error occured in getData: ', e )
        #db.rollback()
        data = None

    finally:
        #print('finally close')
        if db:
            db.close()

    #print( '[getData] return data:', data, '/type:', type(data) )
    return data


def getDeleteKeyInRows( rows, delKey ):
# Dictionary 여러줄(rows)에 들어있는 field(delKey)를 제거.
    for i in range( 0, len(rows)-1 ):

        if delKey in rows[i]:
            del rows[i][delKey]


def getDeleteKeyInRow( row, delKey ):
#Dictionary 하나의 줄(row)에 있는 field(delKey)를 제거.
    if delKey in row:
        del row[delKey]


def getTableList( description, delKey, rows ):
# Dictionary 여러줄(rows_에 들어있는 field(delKey)를 제거.
# field를 가져오기 위해 cursor.description을 이용.
    #print( 'description:', description, 'delKey:', delKey )

    fieldName = []
    for field in description:
        if ( field[0] != delKey ):
            fieldName.append( field[0] )
            #print( field[0] )

    fieldCount = len( fieldName )
    #print( 'fieldCount:', fieldCount )

    tableList = []

    #print( 'rows:', len(rows), rows )
    for row in rows:

        tableValue = {}
        for i in range( 0, fieldCount ):
            tableValue[ fieldName[i] ] = '' if ( row[fieldName[i]] is None ) else row[ fieldName[i] ]
        #print( tableValue )

        tableList.append( tableValue )

    return tableList


def getWhere( tableName, tableValue ):
    #return  tableName + " = '" + tableValue + "'"
    return  tableName + " = " + getQuotation( tableValue ) + str( tableValue ) + getQuotation( tableValue )


def getWhereSQL( where ):
# { 'field': value } -> field = 'value'형식으로 변환
    if ( type(where) == list ):

        sql = ''
        addAND = 1

        for subWhere in where:

            sql += getWhereField( subWhere )
            sql += ' AND ' if ( addAND < len(where) ) else ''
            addAND += 1

    else:

        sql = getWhereField( where )

    return sql


def getWhereField( where ):
# { 'field': value } -> field = 'value'형식으로 변환
    for field in where:
        quotation = getQuotation( where[field] )
        sql = field + " = " + quotation + str( where[field] ) + quotation

    return sql

def getQuotation( value ):
# value가 숫자인 경우에만 따옴표를 붙이지 않는다.
    return( "" if ( type(value) is int ) else "'" )

def getStr2Int( str ):
# str이 문자형인 경우 숫자로 되돌려 준다, 빈공백은 0으로
    return int(str) if ( str.isdigit() ) else 0

def afterPost( str ):
# post한 str내에서 ampersand(/@)를 &로 바꾼다.
    return str.replace( SIGN_AMPERSAND, '&' ).replace( SIGN_SHARP, '#' )

def removeMark( txt ):
    retTxt = txt.replace( "\n\n\n", "\n" )
    retTxt = retTxt.replace( "`", "'" )
    retTxt = retTxt.replace( "·", "," )
    retTxt = retTxt.replace( "\"", "'" )
    retTxt = retTxt.replace( "''", "'" )
    retTxt = retTxt.replace( "”", "'" )
    retTxt = retTxt.replace( "“", "'" )
    retTxt = retTxt.replace( "/[\x00-\x08\x0E-\x1F\x7F]+/", '' )
    retTxt = retTxt.strip()
    return retTxt
