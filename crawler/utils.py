import re


def clean_text(text):
    """
    clean text function
    ===================

    Arguments
    ---------
    text: str
        text to clean

    Returns
    -------
    text: str
        cleaned text
    """
    # 개행 문자 및 다중공백 제거
    text = re.sub(r"\s+", " ", text)
    # E-mail 제거
    text = re.sub(r"([\w\d.]+@[\w\d.]+)", "", text)
    text = re.sub(r"([\w\d.]+@)", "", text)
    # 괄호 안 제거
    text = re.sub(r"([\(\[]).*?([\)\]])", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    # 전화번호 제거
    text = re.sub(r"(\d{2,3})-(\d{3,4}-\d{4})", "", text)  # 전화번호
    text = re.sub(r"(\d{3,4}-\d{4})", "", text)  # 전화번호
    # 홈페이지 주소 제거
    text = re.sub(r"(www.\w.+)", "", text)
    text = re.sub(r"(.\w+.com)", "", text)
    text = re.sub(r"(.\w+.co.kr)", "", text)
    text = re.sub(r"(.\w+.go.kr)", "", text)
    # 기자 이름 제거
    text = re.sub(r"/\w+[=·\w@]+\w+\s[=·\w@]+", "", text)
    text = re.sub(r"\w{2,4}\s기자", "", text)
    # 한자 제거
    text = re.sub(r"[\u2E80-\u2EFF\u3400-\u4DBF\u4E00-\u9FBF\uF900]+", "", text)
    # 특수기호 제거
    text = re.sub(r"[◇#/▶▲◆■●△①②③★○◎▽=▷☞◀ⓒ□?㈜♠☎]", "", text)
    # 따옴표 제거
    text = re.sub(r"[\"'”“‘’]", "", text)
    return text.strip()