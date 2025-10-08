from __future__ import annotations

import json
import logging
import threading
from collections import defaultdict
from datetime import timedelta, timezone as dt_timezone
from time import monotonic, sleep
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

import requests
from requests import Response
from django.conf import settings
from django.utils import timezone

from ..constants import BASE_URL, DEFAULT_TIMEOUT, OPEN_API_BASE_URL, DEFAULT_DIMISSION_ROSTER_FIELDS
from ..models import DingTalkConfig
from .exceptions import DingTalkAPIError, DingTalkConfigurationError

logger = logging.getLogger(__name__)

# 进程内速率控制
_rate_lock = threading.Lock()
_rate_state: dict[Tuple[str, str], dict[str, float | int]] = defaultdict(lambda: {"timestamp": 0.0, "count": 0})

_DEFAULT_ROSTER_FIELDS: tuple[str, ...] = DEFAULT_DIMISSION_ROSTER_FIELDS


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


def _chunk_iterable(iterable: Iterable[Any], size: int) -> Iterable[list[Any]]:
    chunk: list[Any] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


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

    def _request_open_api(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = params.copy() if params else {}
        payload = data.copy() if data else None
        token = access_token or self.get_access_token()
        url = path if path.startswith("http") else f"{OPEN_API_BASE_URL}{path}"
        headers = {
            "Content-Type": "application/json;charset=utf-8",
            "x-acs-dingtalk-access-token": token,
        }
        try:
            response: Response = self.session.request(
                method,
                url,
                params=params if method.upper() == "GET" else None,
                json=payload if method.upper() != "GET" else None,
                timeout=self.timeout,
                headers=headers,
            )
        except requests.RequestException as exc:  # pragma: no cover
            raise DingTalkAPIError(f"钉钉开放接口网络异常: {exc}") from exc

        if response.status_code >= 500:  # pragma: no cover
            raise DingTalkAPIError(f"钉钉开放接口服务异常: {response.status_code}")

        try:
            result = response.json()
        except ValueError as exc:
            raise DingTalkAPIError("钉钉开放接口返回非 JSON 数据", payload={"text": response.text}) from exc

        if isinstance(result, dict) and result.get("code") not in (None, "0"):
            message = result.get("message") or result.get("msg") or "钉钉开放接口调用失败"
            raise DingTalkAPIError(f"{message}(code={result.get('code')})", payload=result)
        if not isinstance(result, dict):
            raise DingTalkAPIError("钉钉开放接口返回格式异常", payload={"raw": result})
        return result

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

    # --------------------------- 离职人员接口 --------------------------- #
    def list_dimission_userids(self, *, max_results: int = 50) -> list[str]:
        try:
            return self._list_dimission_userids_open_api(max_results=max_results)
        except DingTalkAPIError as exc:
            logger.warning("fallback to legacy dimission user api: %s", exc)
            return self._list_dimission_userids_legacy(max_results=max_results)

    def list_dimission_infos(self, userids: Iterable[str]) -> list[Dict[str, Any]]:
        try:
            return self._list_dimission_infos_open_api(userids)
        except DingTalkAPIError as exc:
            logger.warning("fallback to legacy dimission info api: %s", exc)
            return self._list_dimission_infos_legacy(userids)

    def list_roster_infos(
        self,
        userids: Iterable[str],
        *,
        field_codes: Sequence[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        normalized_ids = [str(u) for u in userids if u]
        if not normalized_ids:
            return {}

        unique_ids = list(dict.fromkeys(normalized_ids))
        fields = list(dict.fromkeys(field_codes or _DEFAULT_ROSTER_FIELDS))
        if not fields:
            return {}

        try:
            raw_items = self._list_roster_infos_open_api(unique_ids, fields)
        except DingTalkAPIError as exc:
            logger.warning("fallback to legacy roster api: %s", exc)
            raw_items = self._list_roster_infos_legacy(unique_ids, fields)

        roster_map: dict[str, dict[str, Any]] = {}
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            userid = str(item.get("userId") or item.get("userid") or "")
            if not userid:
                continue
            field_data_list = item.get("fieldDataList") or item.get("field_data_list") or []
            parsed: dict[str, Any] = {}
            if isinstance(field_data_list, list):
                for field_entry in field_data_list:
                    if not isinstance(field_entry, dict):
                        continue
                    code = field_entry.get("fieldCode") or field_entry.get("field_code")
                    if not code:
                        continue
                    values_raw = field_entry.get("fieldValueList") or field_entry.get("field_value_list") or []
                    value = None
                    label = None
                    normalized_values: list[Any] = []
                    if isinstance(values_raw, list) and values_raw:
                        first = values_raw[0]
                        if isinstance(first, dict):
                            label = first.get("label")
                            value = first.get("value") or label
                        else:
                            value = first
                        for item_value in values_raw:
                            if isinstance(item_value, dict):
                                normalized_values.append(item_value.get("value") or item_value.get("label"))
                            else:
                                normalized_values.append(item_value)
                    elif values_raw not in (None, ""):
                        value = values_raw
                        normalized_values = [values_raw]
                    if value in (None, "") and label in (None, ""):
                        continue
                    parsed[code] = {
                        "value": value,
                        "label": label,
                        "values": [v for v in normalized_values if v not in (None, "")],
                    }
            roster_map[userid] = parsed
        return roster_map

    # --- 新版 OpenAPI --- #
    def _list_dimission_userids_open_api(self, *, max_results: int = 50) -> list[str]:
        max_results = max(1, min(int(max_results), 100))
        params: dict[str, Any] = {"maxResults": max_results}
        userids: list[str] = []
        next_token: Optional[str] = None
        while True:
            query = params.copy()
            if next_token:
                query["nextToken"] = next_token
            _respect_rate_limit("dimission-list", self.config.id)
            payload = self._request_open_api("GET", "/v1.0/hrm/employees/dismissions", params=query)
            user_list = payload.get("userIdList") or []
            userids.extend(str(u) for u in user_list if u)
            has_more = payload.get("hasMore")
            next_token = payload.get("nextToken")
            if not has_more or not next_token:
                break
        return list(dict.fromkeys(userids))

    def _list_dimission_infos_open_api(self, userids: Iterable[str]) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        for batch in _chunk_iterable([str(u) for u in userids if u], 50):
            if not batch:
                continue
            _respect_rate_limit("dimission-info", self.config.id)
            params = {"userIdList": json.dumps(batch, ensure_ascii=False)}
            data = self._request_open_api("GET", "/v1.0/hrm/employees/dimissionInfos", params=params)
            data_list = data.get("result") or data.get("data") or []
            if isinstance(data_list, dict):
                data_list = data_list.get("records") or []
            for item in data_list:
                if isinstance(item, dict):
                    results.append(item)
        return results

    # --- 旧版 TopAPI 兼容 --- #
    def _list_dimission_userids_legacy(self, *, max_results: int = 50) -> list[str]:
        token = self.get_access_token()
        offset = 0
        size = max(1, min(int(max_results), 50))
        userids: list[str] = []
        while True:
            _respect_rate_limit("dimission-list", self.config.id)
            payload = self._request(
                "POST",
                "/topapi/smartwork/hrm/employee/querydimission",
                data={"offset": offset, "size": size},
                access_token=token,
            )
            result = payload.get("result") or {}
            userid_list = result.get("userid_list") or result.get("useridList") or []
            userids.extend([str(u) for u in userid_list if u])
            has_more = result.get("has_more") or result.get("hasMore")
            if not has_more:
                break
            offset += size
        return list(dict.fromkeys(userids))

    def _list_dimission_infos_legacy(self, userids: Iterable[str]) -> list[Dict[str, Any]]:
        token = self.get_access_token()
        results: list[Dict[str, Any]] = []
        for batch in _chunk_iterable([u for u in userids if u], 50):
            _respect_rate_limit("dimission-info", self.config.id)
            payload = self._request(
                "POST",
                "/topapi/smartwork/hrm/employee/listdimission",
                data={"userid_list": ",".join(batch)},
                access_token=token,
            )
            result = payload.get("result") or {}
            data_list = result.get("data_list") or result.get("dataList") or []
            for item in data_list:
                if isinstance(item, dict):
                    results.append(item)
        return results

    def _list_roster_infos_open_api(self, userids: Sequence[str], field_codes: Sequence[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for batch in _chunk_iterable(userids, 50):
            if not batch:
                continue
            _respect_rate_limit("roster-info", self.config.id, limit=10)
            payload: dict[str, Any] = {
                "userIdList": batch,
                "fieldFilterList": field_codes,
                "text2SelectConvert": True,
            }
            if self.config.agent_id:
                payload["appAgentId"] = self.config.agent_id
            data = self._request_open_api("POST", "/v1.0/hrm/rosters/lists/query", data=payload)
            records = data.get("result") or data.get("data") or data.get("records") or data.get("body")
            if isinstance(records, dict):
                records = records.get("data") or records.get("records")
            if not isinstance(records, list):
                continue
            for item in records:
                if isinstance(item, dict):
                    results.append(item)
        return results

    def _list_roster_infos_legacy(self, userids: Sequence[str], field_codes: Sequence[str]) -> list[dict[str, Any]]:
        token = self.get_access_token()
        results: list[dict[str, Any]] = []
        for batch in _chunk_iterable(userids, 50):
            if not batch:
                continue
            _respect_rate_limit("roster-info", self.config.id, limit=10)
            payload: dict[str, Any] = {
                "userid_list": ",".join(batch),
                "field_filter_list": list(field_codes),
                "text2select_convert": True,
            }
            if self.config.agent_id:
                payload["agentid"] = self.config.agent_id
            data = self._request(
                "POST",
                "/topapi/smartwork/hrm/employee/v2/list",
                data=payload,
                access_token=token,
            )
            body = data.get("result") or {}
            records = body.get("data_list") or body.get("dataList") or []
            for item in records:
                if isinstance(item, dict):
                    results.append(item)
        return results

    def list_dimission_records(
        self,
        *,
        start_time: timezone.datetime | None = None,
        end_time: timezone.datetime | None = None,
        max_results: int = 200,
    ) -> list[Dict[str, Any]]:
        if end_time and start_time and start_time > end_time:
            raise DingTalkAPIError("开始时间不能晚于结束时间")

        tz = dt_timezone.utc
        now = timezone.now()
        if end_time is None:
            end_time = now
        if start_time is None:
            start_time = end_time - timedelta(days=365)

        def _format(value: timezone.datetime) -> str:
            aware = value
            if timezone.is_naive(aware):
                aware = timezone.make_aware(aware, timezone.get_current_timezone())
            return aware.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")

        formatted_start = _format(start_time)
        formatted_end = _format(end_time)

        def _normalize_page_size(value: int) -> int:
            try:
                return max(1, min(int(value), 50))
            except (TypeError, ValueError):
                return 20

        def _is_invalid_max_results_error(error: DingTalkAPIError) -> bool:
            payload = getattr(error, "payload", None)
            code = ""
            if isinstance(payload, dict):
                code = str(payload.get("code") or payload.get("Code") or "")
            message = str(error)
            target = "invalidmaxresults"
            return code.lower() == target or target in message.lower()

        def _fetch(page_size: int) -> list[Dict[str, Any]]:
            params = {
                "fromDate": formatted_start,
                "toDate": formatted_end,
                "startTime": formatted_start,
                "endTime": formatted_end,
                "maxResults": _normalize_page_size(page_size),
            }
            next_token: Optional[str] = None
            records: list[Dict[str, Any]] = []
            while True:
                query = params.copy()
                if next_token:
                    query["nextToken"] = next_token
                _respect_rate_limit("dimission-records", self.config.id, limit=10, interval=1.0)
                payload = self._request_open_api("GET", "/v1.0/contact/empLeaveRecords", params=query)
                items = payload.get("records") or payload.get("data") or []
                if isinstance(items, dict):
                    items = items.get("records") or []
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            records.append(item)
                next_token_ = payload.get("nextToken") or payload.get("next_token")
                if not next_token_:
                    break
                next_token = next_token_
            return records

        page_size = _normalize_page_size(max_results)
        try:
            return _fetch(page_size)
        except DingTalkAPIError as exc:
            if _is_invalid_max_results_error(exc) and page_size > 20:
                fallback_size = 20
                logger.warning(
                    "钉钉离职记录接口拒绝 maxResults=%s，改用 fallback=%s (config=%s)",
                    page_size,
                    fallback_size,
                    self.config.id,
                )
                return _fetch(fallback_size)
            raise

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
