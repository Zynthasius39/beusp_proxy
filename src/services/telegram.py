import asyncio

from controller import aioreq

res = asyncio.run(
    wrapper(
        {
            "method": "GET",
            "url": f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe",
        }
    )
)

print(res["response"])