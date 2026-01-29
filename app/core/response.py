from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi import status as http_status

T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    code: int = Field(200, description="业务状态码, 0 表示成功")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = None

def Success(data: Any = None, message: str = "success", code: int = 0):
    """
    统一成功响应
    """
    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content={
            'code': code,
            'message': message,
            'data': data,
        }
    )

def Fail(message: str = "fail", code: int = 50001, status_code: int = http_status.HTTP_500_INTERNAL_SERVER_ERROR):
    """
    统一失败响应
    """
    return JSONResponse(
        status_code=status_code,
        content={
            'code': code,
            'message': message,
            'data': None,
        }
    )
