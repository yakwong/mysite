from __future__ import annotations

import logging
import threading
from collections import defaultdict
from time import monotonic, sleep
from typing import Any, Dict, Iterable, Optional, Tuple

import requests
from requests import Response
from django.conf import settings
from django.utils import timezone

from ..constants import BASE_URL, DEFAULT_TIMEOUT
from ..models import DingTalkConfig
from .exceptions import DingTalkAPIError, DingTalkConfigurationError

logger = logging.getLogger(__name__)

# 进程内速率控制
_rate_lock = threading.Lock()
_rate_state: dict[Tuple[str, str], dict[str, float | int]] = defaultdict(lambda: {"timestamp": 0.0, "count": 0})


def _respect_rate_limit(bucket: str, config_id: str, *, limit: int = 15, interval: float = 1.0) -> None:
    """简单的滑动窗口节流，避免钉钉接口在 1 秒内被调用超过限制."""

    key = (config_id, bucket)
    with _rate_lock:
        state = _rate_state[key]
        now = monotonic()
        timestamp = float(state.get("timestamp", 0.0))
        count = int(state.get("count", 0))

        if now - timestamp >= interval:
            state["timestamp"] = now
            state["count"] = 1
            return

        if count >= limit:
            wait = interval - (now - timestamp) + 0.05
            if wait > 0:
                sleep(wait)
            now = monotonic()
            state["timestamp"] = now
            state["count"] = 1
        else:
            state["count"] = count + 1


class DingTalkClient:
    """基于 requests 的钉钉开放平台客户端"""

    def __init__(
        self,
        config: DingTalkConfig,
        *,
        timeout: int | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config
        if not self.config.app_key or not self.config.app_secret:
            raise DingTalkConfigurationError("请先配置钉钉 AppKey/AppSecret")
        self.timeout = timeout or getattr(settings, "DINGTALK", {}).get("DEFAULT_TIMEOUT", DEFAULT_TIMEOUT)
        self.session = session or requests.Session()
        proxies = getattr(settings, "DINGTALK", {}).get("PROXY")
        if proxies:
            self.session.proxies.update(proxies)

    # --------------------------- 基础 HTTP 封装 --------------------------- #
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = params.copy() if params else {}
        if access_token:
            params.setdefault("access_token", access_token)
        url = f"{BASE_URL}{path}"
        headers = {"Content-Type": "application/json;charset=utf-8"}

        try:
            response: Response = self.session.request(
                method,
                url,
                params=params,
                json=data,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - 网络错误
            raise DingTalkAPIError(f"钉钉接口网络异常: {exc}") from exc

        if response.status_code >= 500:  # pragma: no cover - 钉钉返回500
            raise DingTalkAPIError(f"钉钉接口服务异常: {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise DingTalkAPIError("钉钉接口返回非 JSON 数据", payload={"text": response.text}) from exc

        if isinstance(payload, dict) and payload.get("errcode") not in (0, None):
            errmsg = payload.get("errmsg", "钉钉接口调用失败")
            raise DingTalkAPIError(f"{errmsg}(errcode={payload.get('errcode')})", payload=payload)
        if not isinstance(payload, dict):
            raise DingTalkAPIError("钉钉接口返回格式异常", payload={"raw": payload})
        return payload

    # --------------------------- 令牌管理 --------------------------- #
    def get_access_token(self, *, force_refresh: bool = False) -> str:
        if not force_refresh and self.config.access_token and self.config.access_token_expires_at:
            if self.config.access_token_expires_at - timezone.now() > timezone.timedelta(minutes=2):
                return self.config.access_token

        payload = self._request(
            "GET",
            "/gettoken",
            params={
                "appkey": self.config.app_key,
                "appsecret": self.config.app_secret,
            },
        )
        access_token = payload.get("access_token", "")
        expires_in = int(payload.get("expires_in", 7200))
        expires_at = timezone.now() + timezone.timedelta(seconds=max(expires_in - 60, 60))
        self.config.access_token = access_token
        self.config.access_token_expires_at = expires_at
        self.config.save(update_fields=["access_token", "access_token_expires_at", "update_time"])
        return access_token

    # --------------------------- 部门接口 --------------------------- #
    def get_department(self, dept_id: int, *, access_token: str | None = None) -> Dict[str, Any]:
        token = access_token or self.get_access_token()
        response = self._request(
            "POST",
            "/topapi/v2/department/get",
            data={"dept_id": dept_id, "language": "zh_CN"},
            access_token=token,
        )
        result = response.get("result")
        return result if isinstance(result, dict) else {}

    def list_departments(self, root_dept_id: int = 1) -> list[Dict[str, Any]]:
        token = self.get_access_token()
        visited: set[int] = set()
        results: list[Dict[str, Any]] = []

        def _walk(dept_id: int) -> None:
            payload = self._request(
                "POST",
                "/topapi/v2/department/listsub",
                data={"dept_id": dept_id, "language": "zh_CN"},
                access_token=token,
            )
            result_obj = payload.get("result")
            if isinstance(result_obj, dict):
                dept_list = result_obj.get("dept_list") or []
            elif isinstance(result_obj, list):
                dept_list = result_obj
            else:
                dept_list = []
            for dept in dept_list:
                if not isinstance(dept, dict):
                    continue
                child_dept_id = dept.get("dept_id")
                if child_dept_id is None or child_dept_id in visited:
                    continue
                visited.add(child_dept_id)
                results.append(dept)
                _walk(child_dept_id)

        root_info = self.get_department(root_dept_id, access_token=token)
        if root_info:
            root_id = root_info.get("dept_id", root_dept_id)
            visited.add(root_id)
            results.append(root_info)
            _walk(root_id)
        else:
            _walk(root_dept_id)
        return results

    # --------------------------- 用户接口 --------------------------- #
    def list_users_by_dept(self, dept_id: int, *, size: int = 100) -> list[Dict[str, Any]]:
        token = self.get_access_token()
        cursor = 0
        results: list[Dict[str, Any]] = []
        while True:
            payload = self._request(
                "POST",
                "/topapi/v2/user/list",
                data={
                    "dept_id": dept_id,
                    "cursor": cursor,
                    "size": size,
                    "language": "zh_CN",
                },
                access_token=token,
            )
            result_data = payload.get("result") or {}
            user_list = result_data.get("list") or []
            results.extend(user_list)
            next_cursor = result_data.get("next_cursor")
            if not next_cursor:
                break
            cursor = next_cursor
        return results

    def list_all_users(self, dept_ids: Iterable[int]) -> list[Dict[str, Any]]:
        aggregated: dict[str, dict[str, Any]] = {}
        for dept_id in dept_ids:
            for user in self.list_users_by_dept(dept_id):
                userid = user.get("userid")
                if not userid:
                    continue
                current = aggregated.get(userid)
                if current:
                    dept_id_list = set(current.get("dept_id_list") or [])
                    dept_id_list.update(user.get("dept_id_list") or [])
                    current["dept_id_list"] = sorted(dept_id_list)
                    current.update({k: v for k, v in user.items() if v not in (None, "")})
                else:
                    aggregated[userid] = user
        return list(aggregated.values())

    # --------------------------- 考勤接口 --------------------------- #
    def list_attendance_records(
        self,
        userids: Iterable[str],
        *,
        start_time: timezone.datetime,
        end_time: timezone.datetime,
    ) -> list[Dict[str, Any]]:
        token = self.get_access_token()
        user_list = list(userids)
        if not user_list:
            return []
        batch_size = 50
        results: list[Dict[str, Any]] = []
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        for index in range(0, len(user_list), batch_size):
            batch = user_list[index : index + batch_size]
            offset = 0
            limit = batch_size
            while True:
                retries = 0
                while True:
                    try:
                        _respect_rate_limit("attendance", self.config.id)
                        payload = self._request(
                            "POST",
                            "/attendance/listRecord",
                            data={
                                "userIdList": batch,
                                "userIds": batch,
                                "checkDateFrom": start_str,
                                "checkDateTo": end_str,
                                "isI18n": False,
                                "offset": offset,
                                "limit": limit,
                            },
                            access_token=token,
                        )
                        break
                    except DingTalkAPIError as exc:
                        errcode = exc.payload.get("errcode") if isinstance(exc.payload, dict) else None
                        if errcode == 90018 and retries < 3:
                            backoff = 0.8 + 0.4 * retries
                            logger.warning(
                                "钉钉考勤接口触发限流，准备重试 config=%s offset=%s retries=%s backoff=%.1fs",
                                self.config.id,
                                offset,
                                retries,
                                backoff,
                            )
                            sleep(backoff)
                            retries += 1
                            continue
                        raise
                result_obj = payload.get("result") or payload
                records = []
                has_more_flag = None
                if isinstance(result_obj, dict):
                    records = result_obj.get("recordresult") or []
                    has_more_flag = result_obj.get("has_more")
                    if has_more_flag is None:
                        has_more_flag = result_obj.get("hasMore")
                elif isinstance(result_obj, list):
                    records = result_obj
                if not isinstance(records, list):
                    records = []
                results.extend(records)
                has_more = bool(has_more_flag) if has_more_flag is not None else None
                if len(records) < limit or has_more is False:
                    break
                offset += limit
        return results

    # --------------------------- 回调订阅 --------------------------- #
    def register_event_subscribe(self, events: list[str]) -> Dict[str, Any]:
        token = self.get_access_token()
        payload = {
            "call_back_tag": events,
            "token": self.config.callback_token,
            "aes_key": self.config.callback_aes_key,
            "url": self.config.callback_url,
        }
        return self._request("POST", "/call_back/register_call_back", data=payload, access_token=token)

    def unregister_event_subscribe(self) -> Dict[str, Any]:
        token = self.get_access_token()
        return self._request("POST", "/call_back/delete_call_back", access_token=token)


__all__ = ["DingTalkClient"]
