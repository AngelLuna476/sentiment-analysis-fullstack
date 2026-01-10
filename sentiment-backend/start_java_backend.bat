@echo off
echo Iniciando Back-End Java...
cd /d %~dp0
mvnw.cmd spring-boot:run
pause