import sys

path = 'c:/221761_TIEN_PHONG_TT_VL_2026/frontend/src/services/api.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('export const layNoiDungLandingPublic')
if idx != -1:
    content = content[:idx]

new_block = """\n\nexport const layNoiDungLandingPublic = async () => {
  try {
    const response = await fetch(`${DIA_CHI_API_GOC}/api/landing-content`)
    if (!response.ok) throw new Error('Không thể tải nội dung landing')
    const data = await response.json()
    return { thanhCong: true, content: data.content }
  } catch (error) {
    return { thanhCong: false, loiMessage: error.message }
  }
}
"""

with open(path, 'w', encoding='utf-8') as f:
    f.write(content + new_block)
