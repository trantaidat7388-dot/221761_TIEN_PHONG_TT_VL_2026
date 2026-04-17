export const fmtDate = (v) => (v instanceof Date ? v.toLocaleString('vi-VN') : (v ? new Date(v).toLocaleString('vi-VN') : '-'));

export const fmtSize = (b) => {
  if (!Number.isFinite(b) || b < 0) return '-';
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(1)} MB`;
};

export const fmtVND = (n) => `${new Intl.NumberFormat('vi-VN').format(n || 0)} VND`;

export const avatarChars = (u) => {
  const s = (u?.username || u?.email || '').trim();
  if (!s) return 'U';
  const parts = s.replace(/\s+/g, ' ').split(' ').filter(Boolean);
  return parts.length >= 2 
    ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase() 
    : (parts[0]?.slice(0, 2) || 'U').toUpperCase();
};
