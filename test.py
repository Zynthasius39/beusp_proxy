import time

from beusproxy.services.telegram_proc import TelegramProc

tp = TelegramProc()
print(tp.query("get_me"))
time.sleep(1)
tp.close()