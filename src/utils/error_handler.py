"""
통일된 에러 처리 패턴
프로젝트 전체에서 사용할 커스텀 예외 클래스 및 에러 처리 유틸리티
"""

from typing import Optional, Dict, Any, Union
from enum import Enum
from loguru import logger
import traceback


class ErrorCode(Enum):
    """에러 코드 열거형"""
    # API 관련 에러
    API_CONNECTION_ERROR = "API_CONNECTION_ERROR"
    API_AUTHENTICATION_ERROR = "API_AUTHENTICATION_ERROR"
    API_RATE_LIMIT_ERROR = "API_RATE_LIMIT_ERROR"
    API_INVALID_RESPONSE = "API_INVALID_RESPONSE"
    
    # 데이터베이스 관련 에러
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    DATABASE_CONSTRAINT_ERROR = "DATABASE_CONSTRAINT_ERROR"
    
    # 데이터 검증 에러
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_DATA_TYPE = "INVALID_DATA_TYPE"
    
    # 파일 처리 에러
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_READ_ERROR = "FILE_READ_ERROR"
    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    
    # 비즈니스 로직 에러
    PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND"
    SUPPLIER_NOT_FOUND = "SUPPLIER_NOT_FOUND"
    MARKETPLACE_NOT_FOUND = "MARKETPLACE_NOT_FOUND"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    
    # 일반 에러
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


class BaseAPIError(Exception):
    """API 관련 기본 예외 클래스"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """에러 정보를 딕셔너리로 변환"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None
        }


class APIConnectionError(BaseAPIError):
    """API 연결 에러"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.API_CONNECTION_ERROR,
            details=details
        )


class APIAuthenticationError(BaseAPIError):
    """API 인증 에러"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.API_AUTHENTICATION_ERROR,
            details=details
        )


class DatabaseError(BaseAPIError):
    """데이터베이스 에러"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_CONNECTION_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class ValidationError(BaseAPIError):
    """데이터 검증 에러"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=error_details
        )


class BusinessLogicError(BaseAPIError):
    """비즈니스 로직 에러"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details
        )


class ErrorHandler:
    """에러 처리 유틸리티 클래스"""
    
    @staticmethod
    def handle_api_error(
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> BaseAPIError:
        """
        API 에러 처리
        
        Args:
            error: 원본 에러
            operation: 수행 중이던 작업
            context: 추가 컨텍스트 정보
            
        Returns:
            처리된 API 에러
        """
        context = context or {}
        context["operation"] = operation
        
        # HTTP 상태 코드별 처리
        if hasattr(error, 'status'):
            if error.status == 401:
                return APIAuthenticationError(
                    message=f"API 인증 실패: {operation}",
                    details=context,
                    original_error=error
                )
            elif error.status == 429:
                return BaseAPIError(
                    message=f"API 요청 한도 초과: {operation}",
                    error_code=ErrorCode.API_RATE_LIMIT_ERROR,
                    details=context,
                    original_error=error
                )
            elif error.status >= 500:
                return APIConnectionError(
                    message=f"API 서버 오류: {operation}",
                    details=context,
                    original_error=error
                )
        
        # 연결 관련 에러
        if "connection" in str(error).lower() or "timeout" in str(error).lower():
            return APIConnectionError(
                message=f"API 연결 실패: {operation}",
                details=context,
                original_error=error
            )
        
        # 기본 API 에러
        return BaseAPIError(
            message=f"API 오류: {operation}",
            error_code=ErrorCode.API_INVALID_RESPONSE,
            details=context,
            original_error=error
        )
    
    @staticmethod
    def handle_database_error(
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DatabaseError:
        """
        데이터베이스 에러 처리
        
        Args:
            error: 원본 에러
            operation: 수행 중이던 작업
            context: 추가 컨텍스트 정보
            
        Returns:
            처리된 데이터베이스 에러
        """
        context = context or {}
        context["operation"] = operation
        
        error_message = str(error).lower()
        
        # 제약 조건 위반
        if "constraint" in error_message or "unique" in error_message:
            return DatabaseError(
                message=f"데이터베이스 제약 조건 위반: {operation}",
                error_code=ErrorCode.DATABASE_CONSTRAINT_ERROR,
                details=context,
                original_error=error
            )
        
        # 연결 에러
        if "connection" in error_message:
            return DatabaseError(
                message=f"데이터베이스 연결 실패: {operation}",
                error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
                details=context,
                original_error=error
            )
        
        # 쿼리 에러
        return DatabaseError(
            message=f"데이터베이스 쿼리 오류: {operation}",
            error_code=ErrorCode.DATABASE_QUERY_ERROR,
            details=context,
            original_error=error
        )
    
    @staticmethod
    def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        에러 로깅
        
        Args:
            error: 로깅할 에러
            context: 추가 컨텍스트 정보
        """
        context = context or {}
        
        # 에러 타입별 로깅 레벨 결정
        if isinstance(error, (APIAuthenticationError, ValidationError)):
            log_level = "WARNING"
        elif isinstance(error, (APIConnectionError, DatabaseError)):
            log_level = "ERROR"
        else:
            log_level = "ERROR"
        
        # 로깅 메시지 구성
        log_message = f"Error: {error.message}"
        if context:
            log_message += f" | Context: {context}"
        
        # 스택 트레이스 포함
        if log_level == "ERROR":
            logger.error(f"{log_message}\n{traceback.format_exc()}")
        else:
            logger.warning(log_message)


def safe_async_execute(
    func,
    *args,
    operation: str = "unknown",
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Union[Any, BaseAPIError]:
    """
    안전한 비동기 함수 실행
    
    Args:
        func: 실행할 비동기 함수
        *args: 함수 인자
        operation: 작업 이름
        context: 추가 컨텍스트
        **kwargs: 함수 키워드 인자
        
    Returns:
        함수 결과 또는 에러 객체
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        ErrorHandler.log_error(e, context)
        
        # 에러 타입별 처리
        if "api" in operation.lower():
            return ErrorHandler.handle_api_error(e, operation, context)
        elif "database" in operation.lower() or "db" in operation.lower():
            return ErrorHandler.handle_database_error(e, operation, context)
        else:
            return BaseAPIError(
                message=f"작업 실패: {operation}",
                details=context,
                original_error=e
            )


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: list[str],
    field_name: str = "data"
) -> None:
    """
    필수 필드 검증
    
    Args:
        data: 검증할 데이터
        required_fields: 필수 필드 목록
        field_name: 데이터 이름 (에러 메시지용)
        
    Raises:
        ValidationError: 필수 필드가 누락된 경우
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            message=f"{field_name}에 필수 필드가 누락됨: {', '.join(missing_fields)}",
            field=",".join(missing_fields),
            details={"missing_fields": missing_fields}
        )


def validate_data_type(
    value: Any,
    expected_type: type,
    field_name: str
) -> None:
    """
    데이터 타입 검증
    
    Args:
        value: 검증할 값
        expected_type: 예상 타입
        field_name: 필드 이름
        
    Raises:
        ValidationError: 타입이 맞지 않는 경우
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            message=f"{field_name}의 타입이 올바르지 않음. 예상: {expected_type.__name__}, 실제: {type(value).__name__}",
            field=field_name,
            details={
                "expected_type": expected_type.__name__,
                "actual_type": type(value).__name__,
                "value": str(value)
            }
        )
