#-*- coding:utf-8 -*-

import mysql.connector
import redis

cnx = mysql.connector.connect(user='java_immaster', password='to8to123',
                              host='192.168.1.169', database='t8t_im', port='3333', use_unicode=False, buffered=True)
cursor = cnx.cursor()
rediscon = redis.Redis(host='192.168.3.210', port=6379, db=0, password='')


# 获取所有不同uid
def getAllUids():
    uids = list()
    try:
        sql = 'SELECT uid FROM im_session_status GROUP BY uid'
        cursor.execute(sql)
        result = cursor.fetchall()
        for session_status in result:
            uids.append(session_status[0])
    except mysql.connector.Error as e:
        print(e)
    print(uids)
    return uids

# 根据uid查询该uid下所有session
def getSessionStatusFromUid(uid):
    hmsetResult = dict()
    try:
        sql = 'SELECT session_id, session_type, read_time FROM im_session_status WHERE uid = %s' % (uid)
        cursor.execute(sql)
        results = cursor.fetchall()
        for result in results:
            hmsetResult.setdefault('%s_%s' % (
                result[1], result[0]), str(result[2]))
    except mysql.connector.Error as e:
        print(e)
    return hmsetResult

# 获取所有不同的会话
def getAllSessions():
    try:
        sql = 'SELECT session_id, session_type FROM im_session_status GROUP BY session_id, session_type'
        cursor.execute(sql)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as e:
        print(e)

# 根据session_type, session_id 查询该会话下所有用户
def getUidsBySessionIdAndType(session_id, session_type):
    uids = list()
    try:
        sql = 'SELECT uid FROM im_session_status WHERE session_id = %s AND session_type = %s' % (session_id, session_type)
        cursor.execute(sql)
        results = cursor.fetchall()
        for result in results:
            uids.append(str(result[0]))
    except mysql.connector.Error as e:
        print(e)
    return uids

# 把数据插入到redis
def insertDataToRedis():
    uids = getAllUids()
    for uid in uids:
        hmsetResult = getSessionStatusFromUid(uid)
        rediscon.hmset(str(uid), hmsetResult)
        
    sessions = getAllSessions()
    for session in sessions:
        session_id = session[0]
        session_type = session[1]
        uids = getUidsBySessionIdAndType(session_id, session_type)
        rediscon.sadd('%s_%s' % (session_type, session_id), uids)

def main():
    pass
    
if __name__ == '__main__':
    main()
