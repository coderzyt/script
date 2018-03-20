# -*- coding: utf-8 -*-
import mysql.connector
import redis

def addSessionType():
    cnx = mysql.connector.connect(user='java_immaster', password='to8to123',host='192.168.1.169',database='t8t_im', use_unicode=False, buffered=True)
    cursor = cnx.cursor()
    try:
        sql = 'alter table im_session_status change is_group session_type TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT "会话类型, 枚举含义 0-p2p聊天会话, 1-群聊会话, 2-工作通知会话"'
        cursor.execute(sql)
    except mysql.connector.Error as e:
        print(e)

def createSessionStatus():
    cnx = mysql.connector.connect(user='java_immaster', password='to8to123',host='192.168.1.169',database='t8t_im', use_unicode=False, buffered=True)
    cursor = cnx.cursor()
    for i in range(0, 128):
        try:
            sql = 'CREATE TABLE im_session_status_%s (id int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT "主键id",uid int(10) unsigned NOT NULL COMMENT "用户id",session_id bigint(20) unsigned NOT NULL DEFAULT 0 COMMENT "会话id",session_type tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT "是否是群组, 枚举含义:0-否, 1-是",deleted tinyint(3) unsigned NOT NULL DEFAULT 0 COMMENT "删除TAG, 枚举含义:0-未被删除; 1-自主退群; 2-被移出群聊",read_time bigint(20) unsigned NOT NULL DEFAULT 0 COMMENT "最新读取消息时间",create_time bigint(20) unsigned NOT NULL DEFAULT 0 COMMENT "会话创建时间",delete_time bigint(20) unsigned NOT NULL DEFAULT 0 COMMENT "会话删除TAG时间",PRIMARY KEY (id),UNIQUE KEY uid_sessionId (session_id,uid)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="im|用户会话表|clay.zhao|2017-03-14"' % (i)
            cursor.execute(sql)
            print('创建会话表: im_session_status_%s'%(i))
        except mysql.connector.Error as e:
            print(e)

def moveTheData():
    cnx = mysql.connector.connect(user='java_immaster', password='to8to123',host='192.168.1.169',database='t8t_im', use_unicode=False, buffered=True)
    cursor = cnx.cursor()
    i = 1
    while i > 0:
        result = list()
        try:
            sql = 'select * from im_session_status where id $lt %s and id &gte %s' % (i*1000, (i-1)*1000)
            cursor.execute(sql)
            result = cursor.fetchall()
        except mysql.connector.Error as e:
            print(e)
        if len(result) > 0:
            insertData(result, 1)
            i += 1
        else:
            break

def insertData(data, index):
    cnx = mysql.connector.connect(user='java_immaster', password='to8to123',host='192.168.1.169',database='t8t_im', use_unicode=False, buffered=True)
    cursor = cnx.cursor()
    try:
        sql = 'insert into im_session_status_%s (session_id, uid, session_type, deleted, read_time, create_time, delete_time) values ()' % (index)
        cursor.execute(sql, )
    except mysql.connector.Error as e:
        print(e)

def setHashMap(rediscon):
    for j in range(0, 10000):
        for i in range(0, 128):
            rediscon.hset('clay_%s'%(j), '%s_430853939366506' % (i), '1519800678035')

def setZipList(rediscon):
    for j in range(0, 10000):
        for i in range(0, 10):
            rediscon.lpush('430853939366506_%s'%(j), i)

def main():
    rediscon = redis.Redis(host='192.168.3.210',port=6379,db=0, password='')
    # setHashMap(rediscon)
    setZipList(rediscon)

if __name__ == '__main__':
    main()
