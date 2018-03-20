#!/bin/bash
#####################################################
# File:     control.sh
# Version:  1.0
# Date:     2017-04-01
# Author:   janson.jiang
# Descriptions: start control script for java service
#####################################################

#引全局环境变量
source /etc/profile
#服务启动脚本的路径
CONTROLDIR=`readlink -f $(dirname $0)`
#获取项目名project
APP=`echo ${CONTROLDIR}|awk -F/ '{$NF="";print $0}'|awk '{print $NF}'`
#获取模块名
PROG=`basename ${CONTROLDIR}|awk -F\- '{print $1}'`
#指定日志目录
JAVALOGS="/data/logs/java/logs"
#指定服务启动的out存放文件目录和进程pid存放目录
JAVARUN="/data/logs/java/run"
#获取版本号
VERSION=`cat ${CONTROLDIR}/version|grep 'version'|awk -F= '{print $NF}'`
#如果version没有，则为0
VERSION="${VERSION:-0}"
#idc环境启动内存配置
if [[ $ENV == "idc" ]];then
    #java服务的最小内存
    JAVAXMS="${JAVAXMS:-512m}"
    #java服务的最大内存
    JAVAXMX="${JAVAXMX:-2048m}"
else
    JAVAXMS="${JAVAXMS:-128m}"
    JAVAXMX="${JAVAXMX:-512m}"
fi
#获取本机IP
LOCAL_IP=`ifconfig br1 2>&1| awk '{if ($1~/inet$/) {print substr($2,6)}}'|head -1`
[ -z "$LOCAL_IP" ] && LOCAL_IP=`ifconfig bond1 2>&1| awk '{if ($1~/inet$/) {print substr($2,6)}}'|head -1`
[ -z "$LOCAL_IP" ] && LOCAL_IP=`ifconfig em1 2>&1| awk '{if ($1~/inet$/) {print substr($2,6)}}'|head -1`
[ -z "$LOCAL_IP" ] && LOCAL_IP=`ifconfig eth0 2>&1| awk '{if ($1~/inet$/) {print substr($2,6)}}'|head -1`
#获取UUID(IP_项目_模块_版本号 MD5值)
UUID=`echo "${LOCAL_IP}_${APP}_${PROG}_${VERSION}_$(date +%s)"|md5sum|grep -o '^.\{5\}'`
#项目对应模块的out文件名
APPOUT="${JAVARUN}/${APP}-${PROG}.out"
APPOUTFILE="${JAVARUN}/${APP}-${PROG}-${VERSION}.out"
#项目对应模块的pid文件名
APPIDFILE="${JAVARUN}/${APP}-${PROG}-${VERSION}.pid"
APPID="${JAVARUN}/${APP}-${PROG}.pid"
#项目对应模块的上一次pid的jstack信息
#APPHEAP="${JAVARUN}/${APP}_${PROG}_${VERSION}_${UUID}.heap"
APPHEAP="${JAVARUN}/${APP}-${PROG}-${VERSION}.heap"
#获取项目对应的模块的jar包
COUNT=`ls ${CONTROLDIR}|grep "^${APP}-${PROG}.*.jar$"|wc -l`
if [[ ${COUNT} -eq 1 ]];then
    JAR=`ls ${CONTROLDIR}|grep "^${APP}-${PROG}.*.jar$"`
else
    echo "The start jar is not unique,please contact the administrator"
    exit 1
fi
#指定java命令
if [[ "${JAVA_HOME}" != "" ]];then
    JAVA="${JAVA_HOME}/bin/java"
else
    JAVA=$(which java)
fi
#指定kill命令
if [[ ! -x "${KILL:-/bin/kill}" ]];then
    KILL=/bin/kill
else
    KILL=kill
fi
#保证日志目录和启动输出目录存在
if [[ ! -d "${CONTROLDIR}/var/run" ]];then
    mkdir -p ${JAVARUN}
    mkdir -p ${CONTROLDIR}/var/
    ln -s ${JAVARUN} ${CONTROLDIR}/var/run
fi

if [[ ! -d "$JAVALOGS" ]];then
    mkdir -p ${JAVALOGS}
fi
#libs文件列表
#unzip -ca ${CONTROLDIR}/${JAR} META-INF/MANIFEST.MF|grep '.*.jar'|grep -v "${JAR}"|dos2unix|sed -n 's#[ ]\+##p'|awk BEGIN{RS=EOF}'{gsub(/\n/,"");print}'|sed 's/Class-Path:.//'|sed 's#lib/##g'

libs=`unzip -ca ${CONTROLDIR}/${JAR} META-INF/MANIFEST.MF|grep 'Class-Path:.' -A50|grep -Ev '^$|^Created-By:|^Main-Class:|^Build-Jdk:'|sed -n 's#\r##p'|sed -n 's#[ ]\?##p'|awk BEGIN{RS=EOF}'{gsub(/\n/,"");print}'|sed 's/Class-Path: .//'|sed 's#lib/##g'`

function check_libs()
{
    for lib in ${libs}
    do
        ls ${CONTROLDIR}/lib|grep "${lib}" &> /dev/null
        if [[ $? -ne 0 ]];then
            echo "${lib} is not exist in ${CONTROLDIR}/lib/"
            exit 1
        fi
    done
}

function find_instance()
{
    local al_pid=`cat $1`
    local al_version=`jps -v|grep ${al_pid}|grep -o '\-Djava.apps.version=[0-9]\+'|awk -F\= '{print $2}'`
    echo "this host already running project: <${APP}> module: <${PROG}> version: <${al_version}>."
}

function start()
{
    echo  -e "Starting java app $APP\n instance: $PROG"

    if [[ ! -d ${CONTROLDIR}/../${PROG} ]];then
        cd ${CONTROLDIR}/../ && ln -snf ${PROG}-${VERSION} ${PROG}
    elif [[ -d ${CONTROLDIR}/../${PROG} && -L ${CONTROLDIR}/../${PROG} ]];then
        cd ${CONTROLDIR}/../ && ln -snf ${PROG}-${VERSION} ${PROG}
    fi

    #判断是否存在pid，pid是唯一标识
    if [[ -f "$APPIDFILE" ]];then
        if kill -0 `cat "$APPIDFILE"` > /dev/null 2>&1;then
            echo already running as process `cat "$APPIDFILE"`.
            find_instance ${APPIDFILE}
            exit 0
        fi
    fi
    if [[ -f ${APPID} ]];then
        if kill -0 `cat "$APPID"` > /dev/null 2>&1;then
            echo already running as process `cat "$APPID"`.
            find_instance ${APPID}
            exit 0
        fi
    fi

    check_libs

    #启动java服务
    su - www -c 'nohup "'$JAVA'" \
          -server -Xms"'$JAVAXMS'" -Xmx"'$JAVAXMX'" -Djava.apps.version='$VERSION' \
          "-Djava.run.dir='${JAVARUN}'" "-Djava.logs.dir='${JAVALOGS}'" "-Djava.apps.prog='${APP}-${PROG}'" "-Dinstance.sequence='${UUID}'" -jar '${CONTROLDIR}/${JAR}' > "'$APPOUTFILE'" 2>&1 < /dev/null & echo -e "$!\n" > "'$APPIDFILE'"'

    if [[ $? -eq 0 ]];then
        #将pid输出到pid文件里面
        local pid=`cat $APPIDFILE`
        if [[ $pid != "" ]];then
            sleep 1
            echo STARTED
        else
            echo FAILED TO WRITE PID
            exit 1
        fi
    else
        echo SERVER DID NOT START
        exit 1
    fi
    ln -snf $APPOUTFILE $APPOUT
    ln -snf $APPIDFILE $APPID
    exit 0
}

function stop()
{
    echo -e "Stopping java app $APP\n instance: $PROG"

    if [[ $ENV == "dev" || $ENV == "test" ]];then
        if [[ ! -f "$APPIDFILE" && ! -f ${APPID} ]];then
            echo "no java app $APP to stop (could not find file $APPIDFILE)"
        else
            appid=`cat "$APPID"`
            jstack $appid > "${APPHEAP/%.heap/-${appid}.heap}" 2>&1
            rm -f ${APPOUT}
            mv -f $APPOUTFILE $APPOUTFILE.bak > /dev/null 2>&1
            sleep 0.1

            kill -15 $(cat "$APPID")
            rm -f ${APPIDFILE}
            rm -f $APPID
            echo STOPPED
        fi
    else
        if [[ ! -f "$APPIDFILE" ]];then
            echo "no java app $APP to stop (could not find file $APPIDFILE)"
        else
            appid=`cat "$APPIDFILE"`
            jstack $appid > "${APPHEAP/%.heap/-${appid}.heap}" 2>&1
            rm -f ${APPOUT}
            mv -f $APPOUTFILE $APPOUTFILE.bak > /dev/null 2>&1
            sleep 0.1

            kill -15 $(cat "$APPIDFILE")
            rm -f $APPIDFILE
            rm -f ${APPID}
            echo STOPPED
        fi
    fi
}

function force_stop()
{
    echo -e "Stopping java app $APP\n instance: $PROG"

    if [[ $ENV == "dev" || $ENV == "test" ]];then
        if [[ ! -f "$APPIDFILE" && ! -f ${APPID} ]];then
            echo "no java app $APP to stop (could not find file $APPIDFILE)"
        else
            PID=$(cat $APPID)
            jstack $PID > "${APPHEAP/%.heap/-${appid}.heap}" 2>&1
            rm -f ${APPOUT}
            mv -f $APPOUTFILE $APPOUTFILE.bak
            sleep 0.1

            $KILL -9 $PID
            rm -f ${APPIDFILE}
            rm -f $APPID
            echo STOPPED
        fi
    else
        if [[ ! -f "$APPIDFILE" ]];then
            echo "no java app $APP to stop (could not find file $APPIDFILE)"
        else
            PID=$(cat $APPIDFILE)
            jstack $PID > "${APPHEAP/%.heap/-${appid}.heap}" 2>&1
            rm -f ${APPOUT}
            mv -f $APPOUTFILE $APPOUTFILE.bak
            sleep 0.1

            $KILL -9 $PID
            rm -f ${APPIDFILE}
            rm -f $APPID
            echo STOPPED
        fi
    fi
}

case $1 in
    start)
        start
    ;;
    stop)
        stop
    ;;
    restart)
        stop
        sleep 0.1
        start
    ;;
    force-stop)
        force_stop
    ;;
    *)
        echo $"Usage: $0 {start|stop|restart|force-stop}" >&2
        exit 1
    ;;
esac
