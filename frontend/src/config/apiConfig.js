// apiConfig.js - Cấu hình URL backend dùng chung
// Ưu tiên lấy từ biến môi trường Vite, fallback về localhost cho môi trường dev

export const DIA_CHI_API_GOC =
  import.meta.env?.VITE_API_URL && typeof import.meta.env.VITE_API_URL === 'string'
    ? import.meta.env.VITE_API_URL
    : 'http://localhost:8000'

