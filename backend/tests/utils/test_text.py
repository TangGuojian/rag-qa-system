import pytest
from app.utils.text import (
    extract_chinese_bigrams,
    extract_chinese_words,
    CHINESE_STOP_WORDS,
    CHINESE_STOP_CHARS,
)


class TestTextUtils:
    def test_extract_chinese_bigrams_normal(self):
        result = extract_chinese_bigrams("差旅报销流程")
        assert "差旅" in result
        assert "报销" in result
        assert "流程" in result
        # "旅报" may or may not be in results depending on stop char filter
        # Just check the key expected ones

    def test_extract_chinese_bigrams_mixed(self):
        result = extract_chinese_bigrams("hello差旅2024报销")
        assert "差旅" in result
        assert "报销" in result

    def test_extract_chinese_bigrams_empty_or_no_chinese(self):
        assert len(extract_chinese_bigrams("")) == 0
        assert len(extract_chinese_bigrams("abc123")) == 0
        assert len(extract_chinese_bigrams("一")) == 0

    def test_stop_words_defined(self):
        assert len(CHINESE_STOP_WORDS) > 0
        assert "的" in CHINESE_STOP_WORDS
        assert "了" in CHINESE_STOP_WORDS

    def test_stop_chars_defined(self):
        assert len(CHINESE_STOP_CHARS) > 0

    def test_extract_chinese_bigrams_with_stop_filtered(self):
        result = extract_chinese_bigrams("我的预算")
        assert "预算" in result

    def test_multiple_questions(self):
        bigrams = extract_chinese_bigrams("差旅报销标准是多少")
        assert "差旅" in bigrams
        assert "报销" in bigrams
        assert "标准" in bigrams
