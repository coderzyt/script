# -*- coding: utf-8 -*-

import mysql.connector

cnx = mysql.connector.connect(user='java_immaster', password='to8to123',host='192.168.1.169',database='t8t_im', use_unicode=False, buffered=True)
cursor = cnx.cursor()

# connection = pymysql.connect(host='192.168.1.169',
#                              port=3333,
#                              user='java_immaster',
#                              password='to8to123',
#                              db='t8t_im',
#                              charset='utf8mb4')
# cursor = connection.cursor()

# config = { 'host':'192.168.1.169', 'port':3333, 'user':'java_immaster', 'password':'to8to123', 'db':'t8t_im', 'charset':'utf8mb4', 'cursorclass':pymysql.cursors.DictCursor, } 
# connection = pymysql.connect(**config)

def addColumn():
    for i in range(0, 128):
        try:
            sql = 'ALTER TABLE im_message_%s ADD COLUMN session_type TINYINT(3) UNSIGNED NOT NULL DEFAULT 0 COMMENT "会话类型 枚举含义 0-p2p聊天会话, 1-群聊会话, 2-工作通知会话"'%(i)
            result = cursor.execute(sql)
            print('在im_message_%s中增加字段session_type, 结果为%s'%(i, result))
        except mysql.connector.Error as e:
            print(e)

def dropColumn():
    for i in range(0, 128):
        try:
            sql = 'ALTER TABLE im_message_%s DROP COLUMN session_type'%(i)
            result = cursor.execute(sql)
            print('在im_message_%s中丢弃字段session_type, 结果为%s'%(i, result))
        except mysql.connector.Error as e:
            print(e)

def washData():
    try:
        sql = 'UPDATE im_message_92 session_type = 2 WHERE session_id = 0'
        result1 = cursor.execute(sql)
        print('将im_message_92表中的工作通知session_type改为2, 结果为%s'%(result1))
    except mysql.connector.Error as e:
        print(e)

    for i in range(0, 128):
        try:
            sql = 'UPDATE im_message_%s session_type = 1 WHERE session_id < 10000000'%(i)
            result2 = cursor.execute(sql)
            print('将im_message_%s表中的群聊session_type改为1, 结果为%s'%(i, result2))
        except mysql.connector.Error as e:
            print(e)

def main():
    # addColumn()
    # dropColumn()
    washData()
    # print(cursor)

if __name__ == '__main__':
    main()