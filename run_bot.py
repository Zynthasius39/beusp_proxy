import signal
from multiprocessing import Event

from bot.process import BotProc

shevent = Event()

def handle_shutdown(signum, frame):
        print(f"Bot is shutting down...")
        shevent.set()

# Graceful shutdown
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown) 

with BotProc(shevent=shevent, daemon=False) as bp:
    bp.run()

