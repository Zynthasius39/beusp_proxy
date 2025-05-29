import signal
from multiprocessing import Event

from bot.process import BotProc

shevent = Event()

def handle_shutdown(_, __):
    """Handles Shutdown after a signal is received"""
    print("Bot is shutting down...")
    shevent.set()

# Graceful shutdown
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown) 

with BotProc(shevent=shevent, daemon=False) as bp:
    bp.run()
