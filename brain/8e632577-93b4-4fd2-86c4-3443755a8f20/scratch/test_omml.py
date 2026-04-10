
import os
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def test_omml_insertion():
    doc = Document()
    p = doc.add_paragraph("This is an equation:")
    
    # Simple OMML XML for "a^2 + b^2 = c^2"
    omml_xml_str = """
    <m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <m:r>
        <m:t>a</m:t>
      </m:r>
      <m:sSup>
        <m:e>
          <m:r><m:t></m:t></m:r>
        </m:e>
        <m:sup>
          <m:r><m:t>2</m:t></m:r>
        </m:sup>
      </m:sSup>
      <m:r>
        <m:t> + b</m:t>
      </m:r>
      <m:sSup>
        <m:e>
          <m:r><m:t></m:t></m:r>
        </m:e>
        <m:sup>
          <m:r><m:t>2</m:t></m:r>
        </m:sup>
      </m:sSup>
      <m:r>
        <m:t> = c</m:t>
      </m:r>
      <m:sSup>
        <m:e>
          <m:r><m:t></m:t></m:r>
        </m:e>
        <m:sup>
          <m:r><m:t>2</m:t></m:r>
        </m:sup>
      </m:sSup>
    </m:oMath>
    """
    
    # Try to insert it
    from lxml import etree
    try:
        omml_element = etree.fromstring(omml_xml_str)
        p._element.append(omml_element)
        print("Successfully appended OMML element via lxml")
    except Exception as e:
        print(f"Failed to append: {e}")
        
    output_path = "test_math.docx"
    doc.save(output_path)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    test_omml_insertion()
