from openai import OpenAI
from app.core.config import settings

SYSTEM_PROMPT = """你是企业知识库的RAG问答助手。

【核心规则】
- 你只能使用下方"参考内容"中的信息来回答用户问题
- 你不得使用你自身预训练知识中的任何信息

【回答要求】
1. 严格依据参考内容作答，不得添加参考内容中没有的信息
2. 如果参考内容中有相关信息，请完整、准确地引用并标注文档名称
3. 如果参考内容中没有相关信息，直接回答"未在知识库中找到相关答案"
4. 使用中文回答"""

CHAT_PROMPT = """你是一个友好的智能助手。请用中文自然、简洁地回答用户的问题。
可以进行自由对话、常识问答、计算等，不依赖特定知识库内容。"""


def _make_client(api_key: str | None = None) -> OpenAI:
    return OpenAI(
        api_key=api_key or settings.llm_api_key,
        base_url=settings.llm_api_base,
    )


def _build_rag_messages(question: str, contexts: list[dict], history: list[dict] | None = None) -> list[dict]:
    context_text = "\n\n".join(
        f"[来源: {ctx['filename']}] {ctx['content']}"
        for ctx in contexts
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for h in history[-6:]:
            messages.append({"role": "user", "content": h["question"]})
            messages.append({"role": "assistant", "content": h["answer"]})
    messages.append({"role": "user", "content": f"参考内容：\n{context_text}\n\n问题：{question}"})
    return messages


def generate_answer(
    question: str, contexts: list[dict], api_key: str | None = None,
    temperature: float = 0.3, max_tokens: int = 2048,
    history: list[dict] | None = None,
) -> str:
    client = _make_client(api_key)
    messages = _build_rag_messages(question, contexts, history)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def generate_answer_stream(
    question: str, contexts: list[dict], api_key: str | None = None,
    temperature: float = 0.3, max_tokens: int = 2048,
    history: list[dict] | None = None,
):
    client = _make_client(api_key)
    messages = _build_rag_messages(question, contexts, history)
    stream = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


def _build_chat_messages(question: str, history: list[dict] | None = None) -> list[dict]:
    messages = [{"role": "system", "content": CHAT_PROMPT}]
    if history:
        for h in history[-6:]:
            messages.append({"role": "user", "content": h["question"]})
            messages.append({"role": "assistant", "content": h["answer"]})
    messages.append({"role": "user", "content": question})
    return messages


def chat_direct(
    question: str, api_key: str | None = None,
    temperature: float = 0.7, max_tokens: int = 2048,
    history: list[dict] | None = None,
) -> str:
    client = _make_client(api_key)
    messages = _build_chat_messages(question, history)
    resp = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def chat_direct_stream(
    question: str, api_key: str | None = None,
    temperature: float = 0.7, max_tokens: int = 2048,
    history: list[dict] | None = None,
):
    client = _make_client(api_key)
    messages = _build_chat_messages(question, history)
    stream = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content
