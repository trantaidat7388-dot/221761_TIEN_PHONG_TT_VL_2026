import os
import sys
import asyncio

sys.stdout.reconfigure(encoding='utf-8')
from backend.core_engine.chuyen_doi import ChuyenDoiWordSangLatex
from backend.core_engine.utils import bien_dich_latex, find_main_tex, extract_zip_template

def main():
    docx_path = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Template_word\acm_submission_template.docx"
    template_zip = r"c:\221761_TIEN_PHONG_TT_VL_2026\input_data\Association_for_Computing_Machinery__ACM____SIG_Proceedings_Template.zip"
    out_dir = r"c:\221761_TIEN_PHONG_TT_VL_2026\outputs\test_job"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "images"), exist_ok=True)

    print("Extracting template...")
    try:
        extract_zip_template(template_zip, out_dir)
    except Exception as e:
        pass
    
    template_path = find_main_tex(out_dir)
    out_tex = os.path.join(out_dir, "output.tex")

    print(f"Starting conversion with docx: {docx_path}")
    print(f"Using template: {template_path}")
    
    try:
        bo_chuyen_doi = ChuyenDoiWordSangLatex(
            duong_dan_word=docx_path,
            duong_dan_template=template_path,
            duong_dan_dau_ra=out_tex,
            thu_muc_anh=os.path.join(out_dir, "images"),
            mode='demo'
        )
        bo_chuyen_doi.chuyen_doi()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return
        
    print(f"Conversion finished. Tex file at: {out_tex}")

    def compile():
        print("Starting PDF compilation...")
        thanh_cong, thong_bao_loi = bien_dich_latex(str(out_tex))
        print("Compilation success:", thanh_cong)
        if not thanh_cong:
            print("LaTeX output snippet:", thong_bao_loi[-1000:])
        else:
            print("PDF generated successfully.")

    compile()

if __name__ == "__main__":
    main()
