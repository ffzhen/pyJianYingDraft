"""
自定义异常类

定义工作流中使用的异常类型
"""

class WorkflowError(Exception):
    """工作流基础异常"""
    pass

class ValidationError(WorkflowError):
    """验证错误"""
    pass

class ProcessingError(WorkflowError):
    """处理错误"""
    pass

class DurationError(ValidationError):
    """时长相关错误"""
    pass

class MaterialError(WorkflowError):
    """素材相关错误"""
    pass