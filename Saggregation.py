#-*- coding:utf-8 -*-
#!/usr/bin/python

from sys import argv

ima_Recv2ProcessFile = argv[1]
iml_Recv2StoreFile = argv[2]
iml_transferFile = argv[3]
ima_Forward2ProcessFile = argv[4]

msgByReqID = {}
msgByMsgID = {}
msgTransferByMsgID = {}

msgByUid = {}

h_ima_Recv2ProcessFile = open(ima_Recv2ProcessFile)
h_iml_Recv2StoreFile = open(iml_Recv2StoreFile)
h_iml_transferFile = open(iml_transferFile)
h_ima_Forward2ProcessFile = open(ima_Forward2ProcessFile)

h_SrvFailFile = open("SrvFailFile.txt","w+")

sendSuccNum = 0
sendFailNum = 0
notifyFailNum = 0
recvFailNum = 0


time_all = []
time_imaRecv2imaEndProcess = []
time_imaEndProcess2imlStartConsume = []
time_imlStartConsume2imlEndCheck = []
time_imlEndCheck2imlEndInsertDB=[]
time_imlEndInsertDB2imlStartTransfer=[]
time_imlStartTransfer2imlEndCheckOnline=[]
time_imlEndCheckOnline2imlEndReqTransfer=[]
tim_all_min=[]
time_imaRecvTransfer2imaEndTransferTime=[]

def timeDistribution(timeList):
    _lt50 = 0
    _50_to_100 = 0
    _100_to_200 = 0
    _200_to_400 = 0
    _400_to_800 = 0
    _800_to_1600 = 0
    _1600_to_3200 = 0
    _gt3200 = 0

    count = 0

    for _time in timeList:
        count += 1
        if _time < 3:
            _lt50 += 1
        elif (_time >=3  and _time <6):
            _50_to_100 += 1
        elif (_time >=6  and _time <12):
            _100_to_200 +=1
        elif (_time >=12 and _time <24):
            _200_to_400 +=1
        elif (_time >=24 and _time <48):
            _400_to_800 +=1
        elif (_time >=48 and _time <96):
            _800_to_1600 +=1
        elif (_time >=96 and _time <192):
            _1600_to_3200 +=1
        else:
            _gt3200 += 1


    print "<3ms, 3 ~ 6ms, 6~12ms, 12~24ms, 24~48ms, 48~96ms,96~192ms, >192ms"
    #print "<5ms, 5 ~ 10ms, 10~20ms, 20~40ms, 40~80ms, 80~160ms,160~320ms, >320ms"
    #print "<20ms, 20 ~ 40ms, 40~80ms, 80~160ms, 160~320ms, 320~640ms,640~1280ms, >1280ms"
    #print "<50ms, 50 ~ 100ms, 100~200ms, 200~400ms, 400~800ms, 800~1600ms,1600~3200ms, >3200ms"
    print('%.2f%%,%.2f%%,%.2f%%,%.2f%%,%.2f%%,%.2f%%,%.2f%%,%.2f%%' % (100.00*_lt50/count,100.00*_50_to_100/count,100.00*_100_to_200/count,100.00*_200_to_400/count,100.00*_400_to_800/count,100.00*_800_to_1600/count,100.00*_1600_to_3200/count,100.00*_gt3200/count))
    #print('%2.2f,%2.2f,%.2f,%.2f,%.2f,%.2f,%.2f' % (100*_lt100/count,100*_100_to_200/count,100*_200_to_400/count,100*_400_to_800/count,100*_800_to_1600/count,100*_1600_to_3200/count,100*_gt3200/count))

    return (_lt50,_50_to_100,_100_to_200,_200_to_400,_400_to_800,_800_to_1600,_1600_to_3200,_gt3200)



for line  in h_ima_Recv2ProcessFile:
    _line = line.strip().split()
    sid = int(_line[0])
    did = int(_line[1])
    requestId = int(_line[2])
    msgId = int(_line[3])
    imaRecvTime = int(_line[4])
    imaEndProcessTime = int(_line[5])

    _tup = (msgId,sid,did,requestId,imaRecvTime,imaEndProcessTime)
    msgByMsgID[msgId] = [_tup]


for line in h_iml_Recv2StoreFile:
    _line = line.strip().split()
    sid = int(_line[0])
    did = int(_line[1])
    msgId = int(_line[2])
    imlStartConsumeTime = int(_line[3])
    imlEndCheckTime = int(_line[4])
    imlEndInsertDBTime = int(_line[5])

    if msgId in msgByMsgID:
        _tup = (sid,did,imlStartConsumeTime,imlEndCheckTime,imlEndInsertDBTime)
        msgByMsgID[msgId].append(_tup)
    else:
        sendFailNum += 1
        msgByMsgID[msgId].append(())
        h_SrvFailFile.write("[Fail,File 2] "+line)

for line in h_iml_transferFile:
    _line = line.strip().split()
    msgId = int(_line[2])
    sid = int(_line[0])
    did = int(_line[1])
    imlStartTransferTime = int(_line[3])
    imlEndCheckOnlineTime = int(_line[4])
    imlEndReqTransferTime = int(_line[5])


    if msgId in msgByMsgID:
        _tup = (sid,did,imlStartTransferTime,imlEndCheckOnlineTime,imlEndReqTransferTime)
        msgByMsgID[msgId].append(_tup)
    else:
        sendFailNum += 1
        msgByMsgID[msgId].append(())
        h_SrvFailFile.write("[Fail,File 3] "+line)

for line in h_ima_Forward2ProcessFile:
	_line = line.strip().split()
	msgId = int(_line[2])
	sid = int(_line[0])
	did = int(_line[1])
	imaEndTransferTime = int(_line[4])


	if msgId in msgTransferByMsgID:
		_tup = msgTransferByMsgID[msgId]
		_tup[2] = min(_tup[2], imaEndTransferTime)
		_tup[3] = max(_tup[3], imaEndTransferTime)
	else:
		_tup = [sid,did,imaEndTransferTime,imaEndTransferTime]
		msgTransferByMsgID[msgId] = _tup


#print msgByMsgID[418142040509911041]

print "失败详情"
print " (msgId,sid,did,requestId,imaRecvTime,imaEndProcessTime), (sid,did,imlStartConsumeTime,imlEndCheckTime,imlEndInsertDBTime),(sid,did,imlStartTransferTime,imlEndCheckOnlineTime,imlEndReqTransferTime),(sid,did,imaRecvTransferTime,imaEndTransferTime)"

for _msgId,_msgValue in msgByMsgID.items():
    sendSuccNum += 1
    if len(_msgValue) == 3 and len(_msgValue[0]) > 1 and len(_msgValue[1]) > 1 and len(_msgValue[2]) > 1 and _msgId in msgTransferByMsgID:
		imaRecvTime= _msgValue[0][4]
		imaEndProcessTime= _msgValue[0][5]

		imlStartConsumeTime = _msgValue[1][2]
		imlEndCheckTime = _msgValue[1][3]
		imlEndInsertDBTime = _msgValue[1][4]

		imlStartTransferTime = _msgValue[2][2]
		imlEndCheckOnlineTime= _msgValue[2][3]
		imlEndReqTransferTime = _msgValue[2][4]

		_tup = msgTransferByMsgID[msgId]
		minImaRecvTransferTime = _tup[2]
		maxImaEndTransferTime = _tup[3]

		_time =  maxImaEndTransferTime - imaRecvTime
		time_all.append(_time)

		_time = minImaRecvTransferTime - imlEndReqTransferTime
		tim_all_min.append(_time)

		_time = imaEndProcessTime - imaRecvTime
		time_imaRecv2imaEndProcess.append(_time)

		_time = imlStartConsumeTime - imaEndProcessTime
		time_imaEndProcess2imlStartConsume.append(_time)

		_time = imlEndCheckTime - imlStartConsumeTime
		time_imlStartConsume2imlEndCheck.append(_time)

		_time = imlEndInsertDBTime - imlEndCheckTime
		time_imlEndCheck2imlEndInsertDB.append(_time)

		_time = imlStartTransferTime - imlEndInsertDBTime
		time_imlEndInsertDB2imlStartTransfer.append(_time)

		_time = imlEndCheckOnlineTime - imlStartTransferTime
		time_imlStartTransfer2imlEndCheckOnline.append(_time)


		_time = imlEndReqTransferTime - imlEndCheckOnlineTime
		time_imlEndCheckOnline2imlEndReqTransfer.append(_time)

		_time = imaEndTransferTime - imaRecvTransferTime
		time_imaRecvTransfer2imaEndTransferTime.append(_time)
	else:
		print _msgValue

#################################################
print "                                         "
print "##########################################"
print "处理总数 处理失败 "
print sendSuccNum,sendFailNum


print "                                         "
print "########最后一个收到推送的总耗时分布#####################"
timeDistribution(time_all)

print "                                         "
print "########第一个收到推送的总耗时分布#####################"
timeDistribution(tim_all_min)

print "                                         "
print "######## IMA 收到消息发送请求  ~  IMA处理完成 #####################"
timeDistribution(time_imaRecv2imaEndProcess)

print "                                         "
print "######## IMA处理完成 ~  IML 开始消费#####################"
timeDistribution(time_imaEndProcess2imlStartConsume)

print "                                         "
print "######## IML 开始消费 ~ IML 完成消息合法性验证#####################"
timeDistribution(time_imlStartConsume2imlEndCheck)

print "                                         "
print "######## IML 完成消息合法性验证 ~ IML 完成入库#####################"
timeDistribution(time_imlEndCheck2imlEndInsertDB)

print "                                         "
print "######## IML 消息完成入库 ~ IML 开始转发#####################"
timeDistribution(time_imlEndInsertDB2imlStartTransfer)

print "                                         "
print "######## IML 开始转发 ~ 完成在线状态查询 ####################"
timeDistribution(time_imlStartTransfer2imlEndCheckOnline)

print "                                         "
print "######## IML 完成在线状态查询 ~ IML完成转发请求到IMA#####################"
timeDistribution(time_imlEndCheckOnline2imlEndReqTransfer)

print "                                         "
print "######## IMA收到转发请求 ~ IMA转发成功 #####################"
timeDistribution(time_imaRecvTransfer2imaEndTransferTime)


print "                                         "
print "########异常消息#####################"
h_SrvFailFile = open("SrvFailFile.txt")
for line  in h_SrvFailFile:
    _line = line.strip()
    print _line


h_ima_Recv2ProcessFile.close()
h_iml_Recv2StoreFile .close()
h_iml_transferFile.close()
h_ima_Forward2ProcessFile.close()
h_SrvFailFile.close()
