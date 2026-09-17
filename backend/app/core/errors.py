"""可预期的业务异常。

这些异常会被 API 层翻译成明确的 HTTP 响应，而不是 500 堆栈，
让使用者（尤其是刚跑起项目的同学）知道下一步该做什么。
"""


class MissingApiKeyError(RuntimeError):
    """未配置可用的 AI 服务 Key，无法调用外部模型。"""

    def __init__(self, message: str | None = None):
        super().__init__(message or (
            "尚未配置 AI 服务 API Key。请先进入「个人设置」，"
            "选择服务商并填写你自己的 API Key，保存后重试。"
        ))


class EmbeddingMismatchError(RuntimeError):
    """当前向量模型与知识库中已有向量不兼容（通常是维度不同）。"""

    def __init__(self, message: str | None = None):
        super().__init__(message or (
            "当前向量模型与知识库中已索引的文档不兼容（向量维度不一致）。"
            "请在「个人设置」中把向量模型改回建库时使用的那一个，"
            "或删除原有文档后重新上传。"
        ))
