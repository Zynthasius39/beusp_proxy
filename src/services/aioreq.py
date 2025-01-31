import asyncio
import aiohttp

async def wrapper(rqst):
    """Aiohttp wrapper function

    Args:
        rqst (dict): Request as dictionary

    Returns:
        dict: Response as dictionary
    """
    async with aiohttp.ClientSession() as session:
        return await make_request(session, rqst)


async def n_wrapper(rqsts):
    """Aiohttp wrapper function

    Args:
        rqsts (list): List of request arrays to gather

    Returns:
        list: List of responses
    """
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, req) for req in rqsts]
        return await asyncio.gather(*tasks)


async def make_request(session, req):
    """Aiohttp request function

    Args:
        session (ClientSession): Aiohttp ClientSession
        req (dict): Request as dictionary

    Returns:
        dict: Response as dictionary
    """
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
    except aiohttp.ClientError:
        return None
