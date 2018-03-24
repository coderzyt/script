@echo off

rem ���ּܰ汾��
set archetypeVersion=2.0.0-SNAPSHOT

rem ******************************
echo ����Ϊ������һ��Javaҵ�񹤳���Ŀ����ȷ����Ӧ��ƽ̨��ϵͳ����Ŀ...
set /p platform=ƽ̨��������3����ĸ���룩��
set /p system=ϵͳ��������3����ĸ���룩��
set /p project=��Ŀ��������3����ĸ���룩��

rem ����У���ж�...

set groupId=%platform%.%system%
set artifactId=%platform%-%system%-%project%
set version=1-SNAPSHOT
set package=%platform%.%system%.%project%
set archetypeCatalog=http://ci.we.com/nexus/content/repositories/snapshots/archetype-catalog.xml
mvn org.apache.maven.plugins:maven-archetype-plugin:3.0.0:generate -B -DarchetypeGroupId=com.to8to.platform.archetypes -DarchetypeArtifactId=to8to-archetype-rpc -DarchetypeVersion=%archetypeVersion% -DgroupId=%groupId% -DartifactId=%artifactId% -Dversion=%version% -Dpackage=%package% -DarchetypeCatalog=%archetypeCatalog%


/config/global/listener/permission.user
{
    "uid": 76747
}