import aiohttp
import asyncio

async def wrapper(req):
    async with aiohttp.ClientSession() as session:
        return await make_request(session, req)

async def make_request(session, req):
    try:
        async with session.request(
            method=req["method"],
            url=req["url"],
            headers=req.get("headers"),
            params=req.get("params"),
            json=req.get("json"),
            data=req.get('data'),
            timeout=req.get("timeout", aiohttp.ClientTimeout(total=30)),
            allow_redirects=False,
        ) as response:
            text = await response.text()
            return {
                "status": response.status,
                "headers": response.headers,
                "text": text
            }
    except Exception as e:
        print(f"Request to {req["url"]} failed: {e}")
        return None
