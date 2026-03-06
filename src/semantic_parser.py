import re

def predict_node_type(text, index, is_bold=False):
    """
    Sử dụng TF-IDF & Heuristics nhẹ rút gọn thay vì Machine Learning nặng
    Nhận diện tự động: TITLE, AUTHOR, AFFILIATION, ABSTRACT, KEYWORDS, HEADING
    """
    text = text.strip()
    if not text:
        return "UNKNOWN"
        
    text_lower = text.lower()
    word_count = len(text.split())
    
    # 1. ABSTRACT
    abstract_triggers = ["abstract", "tóm tắt"]
    if word_count < 10 and any(t in text_lower for t in abstract_triggers):
        return "ABSTRACT"
        
    # 2. KEYWORDS
    keyword_triggers = ["keywords", "index terms", "từ khóa"]
    if word_count < 15 and any(t in text_lower for t in keyword_triggers):
        return "KEYWORDS"
        
    # 3. TITLE (Rất ngắn, thường in đậm, nằm ở đầu đoạn)
    # Đoạn đầu tiên hoặc thứ 2, rất ngắn, có thể in đậm hoặc không (vì style đã ẩn b)
    if (index < 10 and word_count <= 25 and is_bold and not text_lower.islower()) or \
       (index < 4 and word_count <= 20 and not text_lower.islower()):
        # Tránh nhầm với Abstract/Keywords
        if not any(t in text_lower for t in abstract_triggers + keyword_triggers):
            return "TITLE"
            
    # 4. AUTHOR (Nằm dưới Title nhỏ hơn 15 từ, tên riêng)
    if 0 < index <= 15 and word_count < 15 and not "university" in text_lower and not "đại học" in text_lower:
        # Nếu có dấu phẩy hoặc chữ C hoa nhiều
        if re.search(r'[A-Z][a-z]+', text):
            return "AUTHOR"
            
    # 5. AFFILIATION (Chứa từ khóa trường học, viện nghiên cứu)
    affiliation_triggers = ["university", "institute", "dept", "department", "đại học", "viện", "khoa", "trường"]
    if 0 < index <= 20 and any(t in text_lower for t in affiliation_triggers):
        return "AFFILIATION"
        
    # 6. REFERENCES HEADER
    ref_triggers = ["references", "tài liệu tham khảo"]
    if word_count < 5 and any(t == text_lower.strip('.: ') for t in ref_triggers):
        return "REFERENCE_HEADER"
        
    # 7. HEADING (Đề mục - I. Introduction)
    if word_count < 15 and is_bold:
        if re.search(r'^((I|II|III|IV|V|VI|VII|VIII|IX|X)+|[1-9]+(\.[1-9]+)*)[\.\:]?\s+[A-Z]', text):
            return "HEADING"
            
    return "PARAGRAPH"
