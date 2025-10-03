# -*- coding: utf-8 -*-

"""
@Remark: 自定义异常处理
"""
import traceback

from django.db.models import ProtectedError
from django.db.utils import DatabaseError
from rest_framework import exceptions
from rest_framework.exceptions import APIException as DRFAPIException, AuthenticationFailed, NotAuthenticated, ValidationError, NotFound
from rest_framework.views import set_rollback, exception_handler
from django.http.response import Http404
from .response import CustomResponse

import logging

logger = logging.getLogger(__name__)


def CustomExceptionHandler(ex, context):
    """
    统一异常拦截处理
    目的:(1)取消所有的500异常响应,统一响应为标准错误返回
        (2)准确显示错误信息
    :param ex:
    :param context:
    :return:
    """
    msg = ""
    response = exception_handler(ex, context)
    if isinstance(ex, AuthenticationFailed):
        if "User is inactive" in str(ex.detail):
            msg = "该账号已被禁用,请联系管理员"
        elif response and response.data.get("detail") == "Given token not valid for any token type":
            msg = "身份认证已过期"
        else:
            msg = ex.detail
    elif isinstance(ex, NotAuthenticated):
        msg = ex.detail
    # elif isinstance(ex,NotFound):
    #     if str(ex)=="无效页面。":
    #         msg="暂无数据"
    #     else:
    #         msg = str(ex)
    elif isinstance(ex, exceptions.ValidationError):
        msg = ex.detail
        errorMsg = msg
        try:
            for key in errorMsg:
                if key:
                    msg = "%s:%s" % (key, errorMsg[key][0])
                else:
                    msg = errorMsg[key][0]
        except:
            # {comment_author: {non_field_errors: ["无效数据。期待为字典类型，得到的是 str 。"]}, images: ["Not a valid string."]}
            if isinstance(errorMsg, list):
                msg = errorMsg[0]
            elif isinstance(errorMsg, dict):
                values_list = list(errorMsg.values())
                keys_list = list(errorMsg.keys())
                if "non_field_errors" in values_list[0]:
                    msg = keys_list[0] + ":" + values_list[0]["non_field_errors"][0]
                elif isinstance(values_list[0], list):
                    msg = keys_list[0] + ":" + values_list[0][0]
                else:
                    msg = errorMsg[0]
            else:
                msg = errorMsg
    elif "django.db.utils.IntegrityError" in str(type(ex)):
        msg = str(ex)
        res = msg.split(", ")
        if res[0] == "(1062":
            msg = "数据有重复，请检查后重试:%s" % msg
    elif isinstance(ex, Http404):
        msg = "404错误：您访问的地址不存在"
    elif isinstance(ex, DRFAPIException):
        set_rollback()
        msg = str(ex.detail)
    elif isinstance(ex, exceptions.APIException):
        set_rollback()
        msg = ex.detail
    elif isinstance(ex, ProtectedError):
        set_rollback()
        msg = "删除失败:该条数据与其他数据有相关绑定"
    # elif isinstance(ex, DatabaseError):
    #     set_rollback()
    #     msg = "接口服务器异常,请联系管理员"
    elif isinstance(ex, Exception):
        msg = str(ex)  # 原样输出错误

    # errorMsg = msg
    # for key in errorMsg:
    #     msg = errorMsg[key][0]
    # print(traceback.format_exc())
    # if response:
    #     return CustomResponse(success=False, data=response.data, msg=msg, status=response.status_code)
    # else:
    #     return CustomResponse(success=False, data={}, msg=msg, status=500)
    return CustomResponse(success=False, data=response.data, msg=msg, status=response.status_code)


class APIException(Exception):
    """
    通用异常:(1)用于接口请求是抛出移除, 此时code会被当做标准返回的code, message会被当做标准返回的msg
    """

    def __init__(self, code=201, message="API异常", args=("API异常",)):
        self.args = args
        self.code = code
        self.message = message

    def __str__(self):
        return self.message
