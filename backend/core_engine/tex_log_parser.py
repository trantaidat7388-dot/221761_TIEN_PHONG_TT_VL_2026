import re

def parse_latex_log(log_text: str) -> dict:
    """
    Phân tích file .log của XeLaTeX để trích xuất dòng lỗi và nguyên nhân cụ thể,
    phục vụ cho Visual Debugger trên Frontend.
    """
    loi = {
        "thanh_cong": False,
        "loai_loi": "KHONG_XAC_DINH",
        "dong": None,
        "thong_diep": "Quá trình biên dịch thất bại nhưng không tìm thấy mã lỗi rõ ràng.",
        "ngu_canh": ""
    }
    
    # Mẫu 1: Bắt lỗi phổ biến (Undefined control sequence, LaTeX Error, Fatal error)
    # Ví dụ:! Undefined control sequence.
    # l.45 \khongtontai
    
    error_pattern = re.compile(r'!\s+(.*?)(?:\n!|\n\s*\n|\Z)', re.DOTALL)
    matches = error_pattern.findall(log_text)
    
    if matches:
        first_err = matches[0].strip()
        lines = first_err.split('\n')
        
        # Trích xuất thông điệp chính
        loi["thong_diep"] = lines[0].strip()
        if "Undefined control sequence" in loi["thong_diep"]:
            loi["loai_loi"] = "SAI_LENH_LATEX"
        elif "LaTeX Error" in loi["thong_diep"]:
            loi["loai_loi"] = "LOI_CU_PHAP_LATEX"
        elif "Fatal error" in loi["thong_diep"]:
            loi["loai_loi"] = "LOI_NGHIEM_TRONG"
        else:
            loi["loai_loi"] = "LOI_BIEN_DICH"
            
        # Tìm dòng bị lỗi (l.123) và ngũ cảnh
        for curr_line in lines[1:]:
            line_match = re.search(r'^l\.(\d+)\s+(.*)', curr_line.strip())
            if line_match:
                loi["dong"] = int(line_match.group(1))
                loi["ngu_canh"] = line_match.group(2).strip()
                break
                
        # Nếu dòng quá dài, chỉ cắt 100 ký tự để ném lên UI
        if len(loi["ngu_canh"]) > 100:
            loi["ngu_canh"] = loi["ngu_canh"][:97] + "..."
    else:
        # Nếu không có pattern !, có thể đây là lỗi font hoặc fatal system crash.
        # Ta sẽ trích xuất 15 dòng cuối để người dùng thấy log thật sự.
        log_lines = log_text.strip().split('\n')
        tail = "\n".join(log_lines[-15:])
        loi["thong_diep"] = f"LỖI HỆ THỐNG (Log Tail):\n{tail}"
        loi["loai_loi"] = "LOI_NGHIEM_TRONG"

    return loi
