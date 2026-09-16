CHINESE_STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "什么",
    "如何", "怎么", "为什么", "哪个", "哪些", "谁",
    "知道", "还是", "就是", "不是", "如果", "因为", "所以", "但是",
    "而且", "或者", "虽然", "然后", "之后", "之前",
}

CHINESE_STOP_CHARS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "看", "好", "这", "他", "她", "它", "们",
    "为", "以", "之", "与", "及", "等", "被", "把", "对", "从",
    "而", "但", "可", "所", "如", "将", "并", "或", "与",
    "什", "么", "没", "知", "还", "就", "不", "是", "如", "因", "所", "但", "而",
    "第", "各", "每",
}


def extract_chinese_bigrams(text: str) -> set[str]:
    chars = [ch for ch in text if "\u4e00" <= ch <= "\u9fff"]
    bigrams = set()
    for i in range(len(chars) - 1):
        bigrams.add(chars[i] + chars[i + 1])
    return {b for b in bigrams if b not in CHINESE_STOP_WORDS}


def extract_chinese_words(text: str, max_words: int = 5, max_len: int = 10) -> list[str]:
    words = []
    buf = ""
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            buf += ch
        else:
            if len(buf) >= 2:
                words.append(buf)
            buf = ""
    if len(buf) >= 2:
        words.append(buf)
    result = [w for w in words if w not in CHINESE_STOP_WORDS and len(w) <= max_len]
    return result[:max_words]
