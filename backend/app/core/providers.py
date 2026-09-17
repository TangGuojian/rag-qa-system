"""可选的大模型服务商预设。

使用者只需在「个人设置」里选一个服务商，界面会自动带出 API 地址与推荐模型，
再填上自己的 Key 即可。所有字段都可以手动改，因此换模型 / 换自建网关都不受限制。

注意：一个能用的 RAG 链路需要「对话模型 + 向量模型」两样。
部分服务商（如 DeepSeek、Moonshot）只提供对话接口，没有向量化接口，
这类服务商会被标记 supports_embedding=False，界面会提示另配向量服务。
"""

PROVIDER_PRESETS: list[dict] = [
    {
        "id": "dashscope",
        "label": "阿里云百炼（DashScope·北京）",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "llm_model": "qwen3.7-plus",
        "embedding_model": "text-embedding-v3",
        "supports_embedding": True,
        "key_url": "https://bailian.console.aliyun.com/?apiKey=1",
        "note": "OpenAI 兼容接口；新用户通常有免费额度，本项目默认对接此服务商。",
    },
    {
        "id": "dashscope-intl",
        "label": "阿里云百炼（DashScope·新加坡）",
        "api_base": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "llm_model": "qwen3.7-plus",
        "embedding_model": "text-embedding-v3",
        "supports_embedding": True,
        "key_url": "https://modelstudio.console.alibabacloud.com/",
        "note": "国际站账号使用；接口与北京站一致。",
    },
    {
        "id": "siliconflow",
        "label": "硅基流动 SiliconFlow",
        "api_base": "https://api.siliconflow.cn/v1",
        "llm_model": "Qwen/Qwen2.5-7B-Instruct",
        "embedding_model": "BAAI/bge-m3",
        "supports_embedding": True,
        "key_url": "https://cloud.siliconflow.cn/account/ak",
        "note": "BAAI/bge-m3 与 Qwen2.5-7B-Instruct 有免费额度，适合零成本试用。",
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "llm_model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-small",
        "supports_embedding": True,
        "key_url": "https://platform.openai.com/api-keys",
        "note": "国内访问需要自备网络代理。",
    },
    {
        "id": "zhipu",
        "label": "智谱 AI（GLM）",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "llm_model": "glm-4-flash",
        "embedding_model": "embedding-3",
        "supports_embedding": True,
        "key_url": "https://bigmodel.cn/usercenter/apikeys",
        "note": "glm-4-flash 有免费额度。",
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "llm_model": "deepseek-chat",
        "embedding_model": None,
        "supports_embedding": False,
        "key_url": "https://platform.deepseek.com/api_keys",
        "note": "只提供对话接口，没有向量化接口：对话模型选它，向量模型需另配（见上方其他服务商）。",
    },
    {
        "id": "moonshot",
        "label": "月之暗面（Kimi）",
        "api_base": "https://api.moonshot.cn/v1",
        "llm_model": "moonshot-v1-8k",
        "embedding_model": None,
        "supports_embedding": False,
        "key_url": "https://platform.moonshot.cn/console/api-keys",
        "note": "只提供对话接口，没有向量化接口，需另配向量服务。",
    },
    {
        "id": "custom",
        "label": "自定义 / 自建网关",
        "api_base": "",
        "llm_model": "",
        "embedding_model": "",
        "supports_embedding": True,
        "key_url": "",
        "note": "任何兼容 OpenAI 协议的地址都可以填，例如本地 Ollama、vLLM、One-API 等。",
    },
]

PROVIDER_BY_ID = {p["id"]: p for p in PROVIDER_PRESETS}
