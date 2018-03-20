#-*- coding:utf-8 -*-
#!/usr/bin/python

from sys import argv

message_send_startFile = argv[1]
message_send_respondedFile = argv[2]
message_noticedFile = argv[3]
message_pullFile = argv[4]

msgByReqID = {}
msgByMsgID = {}

msgByUid = {}

h_send_startFile = open(message_send_startFile)
h_send_respondedFile = open(message_send_respondedFile)
h_noticedFile = open(message_noticedFile)
h_pullFile = open(message_pullFile)

h_msgFailFile = open("msgFailFile.txt","a+")

sendSuccNum = 0
sendFailNum = 0
notifyFailNum = 0
recvFailNum = 0


time_all = []
time_send_recv = []
time_recv_notify = []
time_notify_Pull = []

def timeDistribution(timeList):
    _lt100 = 0
    _100_to_200 = 0
    _200_to_400 = 0
    _400_to_800 = 0
    _800_to_1600 = 0
    _1600_to_3200 = 0
    _gt3200 = 0

    count = 0

    for _time in timeList:
        count += 1
        if _time < 100:
            _lt100 += 1
        elif (_time >=100  and _time <200):
            _100_to_200 +=1
        elif (_time >=200 and _time <400):
            _200_to_400 +=1
        elif (_time >=400 and _time <800):
            _400_to_800 +=1
        elif (_time >=800 and _time <1600):
            _800_to_1600 +=1
        elif (_time >=1600 and _time <3200):
            _1600_to_3200 +=1
        else:
            _gt3200 += 1
   
        
    print("<100ms, 100~200ms, 200~400ms, 400~800ms, 800~1600ms,1600~3200ms, >3200ms")
    print('%.2f%%,%.2f%%,%.2f%%,%.2f%%,%.2f%%,%.2f%%,%.2f%%' % (100.00*_lt100/count,100.00*_100_to_200/count,100.00*_200_to_400/count,100.00*_400_to_800/count,100.00*_800_to_1600/count,100.00*_1600_to_3200/count,100.00*_gt3200/count))
    #print('%2.2f,%2.2f,%.2f,%.2f,%.2f,%.2f,%.2f' % (100*_lt100/count,100*_100_to_200/count,100*_200_to_400/count,100*_400_to_800/count,100*_800_to_1600/count,100*_1600_to_3200/count,100*_gt3200/count))

    return (_lt100,_100_to_200,_200_to_400,_400_to_800,_800_to_1600,_1600_to_3200,_gt3200)



for line  in h_send_startFile:
    _line = line.strip().split()
    requestId = int(_line[0])
    sid = int(_line[1])
    did = int(_line[2])
    sendTime1 = int(_line[3])

    msgByReqID[requestId] = [sid,did,sendTime1]


for line in h_send_respondedFile:
    _line = line.strip().split()
    requestId = int(_line[0])
    sendTime2 = int(_line[1])
    result = int(_line[2])

    if result == 0:
        msgId = int(_line[3])
        sid = msgByReqID[requestId][0]
        did = msgByReqID[requestId][1]
        sendTime1 = msgByReqID[requestId][2]

        tupSend = (requestId,msgId,sid,did,result,sendTime1,sendTime2)
        msgByMsgID[msgId] = [tupSend]

    else:
        sendFailNum += 1
        h_msgFailFile.write("[SendFail] "+line)

for line in h_noticedFile:
    _line = line.strip().split()
    msgId = int(_line[0])
    seqId = int(_line[1])
    sid = int(_line[2])
    did = int(_line[3])
    notifyTime = int(_line[4])
    needPull  = int(_line[5])

    tupNotify = (seqId,sid,did,notifyTime,needPull)
    msgByMsgID[msgId].append(tupNotify)


for line in h_pullFile:
    _line = line.strip().split()
    seqId = int(_line[0])
    msgId = int(_line[1])
    PullTime = int(_line[2])
    result = int(_line[3])
    sid = int(_line[4])
    did = int(_line[5])

    if  result == 1:
        h_msgFailFile.write("[PullFail] "+line)
    else:
        tupPull = (seqId,sid,did,PullTime,result)


        if len(msgByMsgID[msgId])==1:
            msgByMsgID[msgId].append(())
            #notifyFailNum += 1

        msgByMsgID[msgId].append(tupPull)
    

#luan xuan
        tupPull = (msgId,seqId,sid)
        if did in msgByUid:
            msgByUid[did].append(tupPull)
        else:
            msgByUid[did]=[(tupPull),]

#print msgByMsgID[418142040509911041]

print("失败详情")
print("(requestId,msgId,sid,did,result,sendTime1,sendTime2),(seqId,sid,did,notifyTime,needPull),(seqId,sid,did,PullTime,result)")

for _msgId,_msgValue in msgByMsgID.items():
    sendSuccNum += 1

    if len(_msgValue) == 1:
        notifyFailNum += 1
        recvFailNum += 1
        print(_msgValue)

    elif len(_msgValue) == 2:
        recvFailNum += 1
        print(_msgValue)

    else:
        if len(_msgValue[1]) == 0:
            notifyFailNum += 1

        sendTime1 = _msgValue[0][5]
        sendTime2 = _msgValue[0][6]
        notifyTime = _msgValue[1][3]
        pullTime = _msgValue[2][3]

        _time = pullTime - sendTime1
        time_all.append(_time)
        
        _time = sendTime2 - sendTime1
        time_send_recv.append(_time)

        _time =  notifyTime - sendTime2
        time_recv_notify.append(_time)

        _time =  pullTime - notifyTime
        time_notify_Pull.append(_time)

       

        

#################################################
print("                                         ")
print("##########################################")
print("sendSuccNum,sendFailNum,notifyFailNum,recvFailNum")
print(sendSuccNum,sendFailNum,notifyFailNum,recvFailNum) 

        
print("                                         ")
print("########general time distribution#####################")
timeDistribution(time_all)

print("                                         ")
print("########message sending responded time distribution#####################")
timeDistribution(time_send_recv)

print("                                         ")
print("########message notified time distribution#####################")
timeDistribution(time_recv_notify)



print("                                         ")
print("########message pulled time distribution#####################")
timeDistribution(time_notify_Pull)

h_send_startFile.close()
h_send_respondedFile.close()
h_noticedFile.close()
h_pullFile.close()
h_msgFailFile.close()

print("                                         ")
print("########inormal message#####################")
h_msgFailFile = open("msgFailFile.txt")
for line  in h_msgFailFile:
    _line = line.strip()
    print(_line)


print("                                         ")
print("########misorder percentage#####################")
#print msgByUid[100498]
sum = 0
error = 0
for _did,_Value in msgByUid.items():

    
    _msgList = sorted(_Value, key=lambda msg: msg[0])
    firstSeqID = 0
    secondSeqID = 0
    for _msg in _msgList:
        sum  += 1
        secondSeqID = firstSeqID
        firstSeqID = _msg[1]
        
        if firstSeqID < secondSeqID:
            error += 1
            print("%d: %s" % (_did, _msg))

    
print('%.4f%%' % (100.00*error/sendSuccNum))
print('%.4f%%' % (100.00*error/sum))
