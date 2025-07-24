@echo off
cd /d C:\Users\PC\mi-app-humedad
C:\Users\PC\AppData\Local\Programs\Python\Python313\python.exe datos_drop_control.py

git add .
git commit -m "Actualización automática desde tarea programada"
git push
