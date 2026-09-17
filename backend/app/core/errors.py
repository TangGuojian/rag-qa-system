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


class EmbeddingUnsupportedError(RuntimeError):
    """当前服务商不提供向量化接口（如 DeepSeek、Moonshot 只有对话接口）。"""

    def __init__(self, message: str | None = None):
        super().__init__(message or (
            "当前配置的服务商不提供向量化接口，无法为文档建立索引。"
            "请在「个人设置」中换用提供向量模型的服务商"
            "（阿里云百炼 / 硅基流动 / 智谱 / OpenAI），或为向量模型单独配置一个服务商。"
        ))


def humanize_error(exc: Exception) -> str:
    """把 AI SDK 抛出的原始异常翻译成可执行的中文提示。

    先按异常类型判断，再匹配文本。顺序很重要：如果只做文本匹配，
    "unexpected keyword argument 'timeout'" 这类代码缺陷里的字样
    会被误判成网络问题，把真正的 bug 藏起来。
    """
    name = type(exc).__name__
    text = f"{name}: {exc}"
    low = text.lower()

    if name in ("TypeError", "AttributeError", "NameError", "ImportError", "KeyError"):
        return f"服务内部错误（{name}）：{str(exc)[:150]}。这是一处代码缺陷，不是配置问题。"
    if "APIConnectionError" in name or "ConnectTimeout" in name or "APITimeoutError" in name:
        return "无法连接到该服务地址。请检查 API 地址是否写错、本机网络是否可达（境外服务通常需要代理）。"
    if "401" in low or "invalid_api_key" in low or "incorrect api key" in low or "authentication" in low:
        return "API Key 无效或已失效，请检查是否复制完整、是否与该服务商匹配。"
    if "model_not_found" in low or "does not exist" in low or ("404" in low and "model" in low):
        return "模型名不存在。请点「获取可用模型」从服务商返回的列表里选一个。"
    # 404 且发生在向量接口上，几乎总是「该服务商没有 embedding 接口」
    if "404" in low:
        return (
            "接口不存在（404）。若发生在向量化阶段，说明该服务商不提供向量化接口"
            "（如 DeepSeek、Moonshot 只有对话接口）。"
            "请在「个人设置」中换用提供向量模型的服务商：阿里云百炼 / 硅基流动 / 智谱 / OpenAI。"
        )
    if "429" in low or "rate limit" in low or "quota" in low:
        return "请求过于频繁或额度不足，请稍后重试，或检查账户余额。"
    if "insufficient" in low or "arrears" in low or "balance" in low:
        return "账户余额不足，请先充值或更换服务商。"
    if "timed out" in low or "ssl" in low:
        return "连接超时。请检查本机网络是否可达该服务地址（境外服务通常需要代理）。"
    if "not supported" in low or "unsupported" in low:
        return "该服务商不支持这个接口（例如不提供向量化接口），请更换服务商或模型。"
    return f"调用失败：{text[:180]}"
