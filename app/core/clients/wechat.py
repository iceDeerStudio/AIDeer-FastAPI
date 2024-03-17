from aiohttp import ClientSession
from app.core.config import config
from app.core.connections.redis import redis_client
from fastapi import HTTPException
import hashlib
import requests


class Wechat:
    def __init__(self, appid: str, secret: str):
        self.appid = appid
        self.secret = secret

    def wechat_login(self, code) -> tuple[str, str]:
        """
        Get the user's openid and session_key from WeChat.
        """
        url = f"https://api.weixin.qq.com/sns/jscode2session?appid={self.appid}&secret={self.secret}&js_code={code}&grant_type=authorization_code"
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, detail=f"WeChat server error: {response.status_code}"
            )
        data = response.json()
        if "errcode" in data and data["errcode"] != 0:
            raise HTTPException(
                status_code=500,
                detail=f"WeChat server error: {data['errcode']}, {data['errmsg']}",
            )
        openid = data["openid"]
        session_key = data["session_key"]
        return openid, session_key

    def check_wechat_session(self, openid, session_key) -> bool:
        """
        Check the user's openid and session_key from WeChat.
        """
        signature = hashlib.sha256(f"{session_key}{openid}".encode("utf-8")).hexdigest()
        url = f"GET https://api.weixin.qq.com/wxa/checksession?access_token={self.access_token}&signature={signature}&openid={openid}&sig_method=hmac_sha256"
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, detail=f"WeChat server error: {response.status_code}"
            )
        data = response.json()
        if "errcode" in data and data["errcode"] != 0:
            if data["errcode"] == 87009:
                return False
            raise HTTPException(
                status_code=500,
                detail=f"WeChat server error: {data['errcode']}, {data['errmsg']}",
            )
        return True

    def refresh_access_token(self) -> str:
        """
        Get the access token from WeChat and return.
        """
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.secret}"
        response = requests.get(url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, detail=f"WeChat server error: {response.status_code}"
            )
        data = response.json()
        if "errcode" in data:
            raise HTTPException(
                status_code=500,
                detail=f"WeChat server error: {data['errcode']}, {data['errmsg']}",
            )
        redis_client.set(
            "wechat_access_token", data["access_token"], ex=data["expires_in"] - 60
        )
        return data["access_token"]

    def get_access_token(self) -> str:
        """
        Get the access token from Redis. If the access token is not found or is about to expire, refresh it and store it in Redis.
        """
        access_token = redis_client.get("wechat_access_token")
        if not access_token or redis_client.ttl("wechat_access_token") < 300:
            return self.refresh_access_token()
        return access_token

    @property
    def access_token(self) -> str:
        return self.get_access_token()


class WechatAsync:
    def __init__(self, appid: str, secret: str):
        self.appid = appid
        self.secret = secret

    async def wechat_login(self, code) -> tuple[str, str]:
        """
        Get the user's openid and session_key from WeChat.
        """
        url = f"https://api.weixin.qq.com/sns/jscode2session?appid={self.appid}&secret={self.secret}&js_code={code}&grant_type=authorization_code"
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"WeChat server error: {response.status}",
                    )
                data = await response.json()
                if "errcode" in data and data["errcode"] != 0:
                    raise HTTPException(
                        status_code=500,
                        detail=f"WeChat server error: {data['errcode']}, {data['errmsg']}",
                    )
                openid = data["openid"]
                session_key = data["session_key"]
                return openid, session_key

    async def check_wechat_session(self, openid, session_key) -> bool:
        """
        Check the user's openid and session_key from WeChat.
        """
        signature = hashlib.sha256(f"{session_key}{openid}".encode("utf-8")).hexdigest()
        access_token = await self.get_access_token()
        url = f"GET https://api.weixin.qq.com/wxa/checksession?access_token={access_token}&signature={signature}&openid={openid}&sig_method=hmac_sha256"
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"WeChat server error: {response.status}",
                    )
                data = await response.json()
                if "errcode" in data and data["errcode"] != 0:
                    if data["errcode"] == 87009:
                        return False
                    raise HTTPException(
                        status_code=500,
                        detail=f"WeChat server error: {data['errcode']}, {data['errmsg']}",
                    )
                return True

    async def refresh_access_token(self) -> str:
        """
        Get the access token from WeChat and return.
        """
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.secret}"
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"WeChat server error: {response.status}",
                    )
                data = await response.json()
                if "errcode" in data:
                    raise HTTPException(
                        status_code=500,
                        detail=f"WeChat server error: {data['errcode']}, {data['errmsg']}",
                    )
                redis_client.set(
                    "wechat_access_token",
                    data["access_token"],
                    ex=data["expires_in"] - 60,
                )
                return data["access_token"]

    async def get_access_token(self) -> str:
        """
        Get the access token from Redis. If the access token is not found or is about to expire, refresh it and store it in Redis.
        """
        access_token = redis_client.get("wechat_access_token")
        if not access_token or redis_client.ttl("wechat_access_token") < 300:
            return await self.refresh_access_token()
        return access_token


wechat_client = Wechat(config.wechat_appid, config.wechat_secret)
wechat_client_async = WechatAsync(config.wechat_appid, config.wechat_secret)
