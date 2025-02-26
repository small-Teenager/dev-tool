## nginx
    docker run -d -p 80:80 --name dev-nginx nginx
```
 -d参数表示在后台运行容器；
 -p 80:80参数表示将本地的80端口映射到容器的80端口；
 --name dev-nginx参数表示给容器指定一个名称
```
## tomcat
    docker run -d -p --name tomcat 8080:8080 tomcat:8.5
*


     -d参数表示在后台运行容器；
     -p 8080:8080参数表示将本地的8080端口映射到容器的8080端口；
     --name dev-tomcat参数表示给容器指定一个名称
     tomcat:8.5  指定tomcat版本
```
修复tomcat问题 
启动tomcat容器，进入tomcat容器控制台，将webapps.dist替换成webapps
# pwd
/usr/local/tomcat
# ls
bin           conf             lib      logs            NOTICE     RELEASE-NOTES  temp     webapps.dist
BUILDING.txt  CONTRIBUTING.md  LICENSE  native-jni-lib  README.md  RUNNING.txt    webapps  work
# rm -r webapps
# mv webapps.dist webapps            
# ls
bin           conf             lib      logs            NOTICE     RELEASE-NOTES  temp     work
BUILDING.txt  CONTRIBUTING.md  LICENSE  native-jni-lib  README.md  RUNNING.txt    webapps
# 
```

