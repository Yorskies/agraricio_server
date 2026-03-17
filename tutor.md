######menjalankan mosquitto
cd "C:\Program Files\mosquitto"
mosquitto -c mosquitto.conf -v

######melihat prosess yang jalan di port tertentu
netstat -ano | findstr :1883

######membunuh task berdasarkan PID
taskkill /PID 7476 /F