import psutil
import time
import os
import math
import random
from threading import Thread


def get_telly():
    process = psutil.Process(os.getpid())
    while True:
        cpu_temp = "N/A"
        total_cpu_usage = psutil.cpu_percent(interval=0.2)

        # CPU usage of this program
        proc_cpu = process.cpu_percent(interval=0.1)

        # RAM usage of this program
        mem_usage = process.memory_info().rss / (1024 * 1024)  # MB

        print("========== System Stats ==========")
        print(f"CPU Temperature: {cpu_temp} °C")
        print(f"Total CPU Usage: {total_cpu_usage}%")
        print(f"This Program CPU Usage: {proc_cpu}%")
        print(f"This Program Memory Usage: {mem_usage:.2f} MB")
        print("==================================\n")

        time.sleep(1)


def feet():
    n = random.random()
    print("start: ", n)
    while True:
        n = n / n
        # math.pow(n, n)
        print("n: ", n)

# Thread(target=get_telly).start()


thread_count = 0
while thread_count < 10000000:
    thread_count += 1

    Thread(target=feet).start()
