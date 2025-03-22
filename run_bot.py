from bot.process import BotProc

with BotProc(daemon=False) as bp:
    bp.run()