# xu_ly_anh.py - Xử lý phân tích và lọc ảnh (trang trí vs nội dung)

import math
import re
from PIL import Image, ImageStat, ImageFilter

class BoLocAnh:
    # Bộ lọc ảnh: phân biệt ảnh nội dung (photo, chart) và ảnh trang trí (logo, icon)

    # PHÂN TÍCH ẢNH ĐƠN LẺ

    @staticmethod
    def tinh_entropy_anh(duong_dan_hoac_anh) -> float:
        # Tính entropy (Shannon) đo độ hỗn loạn màu: trang trí <3.5, nội dung >5.0
        try:
            if isinstance(duong_dan_hoac_anh, str):
                im = Image.open(duong_dan_hoac_anh)
            else:
                im = duong_dan_hoac_anh
            histogram = im.histogram()
            histogram_length = sum(histogram)
            if histogram_length == 0:
                return 0
            samples_probability = [float(h) / histogram_length for h in histogram]
            entropy = -sum([p * math.log(p, 2) for p in samples_probability if p != 0])
            return entropy
        except Exception as e:
            print(f"[Cảnh báo] Lỗi tinh_entropy_anh: {e}")
            return 0

    @staticmethod
    def tinh_so_mau_anh(duong_dan_hoac_anh) -> int:
        # Đếm số màu duy nhất: logo ít màu (<50), photo nhiều màu (>1000)
        try:
            if isinstance(duong_dan_hoac_anh, str):
                im = Image.open(duong_dan_hoac_anh)
            else:
                im = duong_dan_hoac_anh
            colors = im.getcolors(maxcolors=100000)
            if colors is None:
                return 100000
            return len(colors)
        except Exception as e:
            print(f"[Cảnh báo] Lỗi tinh_so_mau_anh: {e}")
            return 0

    @staticmethod
    def tinh_do_phuc_tap_anh(duong_dan_hoac_anh) -> dict:
        # Phát hiện cạnh (Edge Detection) và đo độ biến thiên (variance)
        try:
            if isinstance(duong_dan_hoac_anh, str):
                im = Image.open(duong_dan_hoac_anh).convert('L')
            else:
                im = duong_dan_hoac_anh.convert('L')
            edges = im.filter(ImageFilter.FIND_EDGES)
            edge_stat = ImageStat.Stat(edges)
            edge_mean = edge_stat.mean[0]
            edge_stddev = edge_stat.stddev[0]

            stat = ImageStat.Stat(im)
            variance = stat.var[0]

            return {
                'edge_mean': edge_mean,
                'edge_stddev': edge_stddev,
                'variance': variance,
            }
        except Exception as e:
            print(f"[Cảnh báo] Lỗi tinh_do_phuc_tap_anh: {e}")
            return {'edge_mean': 0, 'edge_stddev': 0, 'variance': 0}

    @staticmethod
    def phan_tich_histogram(duong_dan_hoac_anh) -> dict:
        # Phân tích histogram: logo ít peaks + dominant cao, photo ngược lại
        try:
            if isinstance(duong_dan_hoac_anh, str):
                im = Image.open(duong_dan_hoac_anh).convert('L')
            else:
                im = duong_dan_hoac_anh.convert('L')
            histogram = im.histogram()
            total = sum(histogram)
            if total == 0:
                return {'num_peaks': 0, 'dominant_ratio': 1.0}

            peaks = 0
            threshold = total * 0.02
            for i in range(1, 255):
                if histogram[i] > threshold:
                    if histogram[i] > histogram[i - 1] and histogram[i] > histogram[i + 1]:
                        peaks += 1

            sorted_hist = sorted(histogram, reverse=True)
            dominant_ratio = sum(sorted_hist[:5]) / total

            return {'num_peaks': peaks, 'dominant_ratio': dominant_ratio}
        except Exception as e:
            print(f"[Cảnh báo] Lỗi phan_tich_histogram: {e}")
            return {'num_peaks': 0, 'dominant_ratio': 1.0}

    # SCORING SYSTEM

    @classmethod
    def la_anh_noi_dung(cls, duong_dan_hoac_anh) -> bool:
        # Tổng hợp điểm từ các tiêu chí: >= 4 = nội dung, < 4 = trang trí (max 12)
        try:
            if isinstance(duong_dan_hoac_anh, str):
                im = Image.open(duong_dan_hoac_anh)
            else:
                im = duong_dan_hoac_anh
                
            entropy = cls.tinh_entropy_anh(im)
            so_mau = cls.tinh_so_mau_anh(im)
            do_phuc_tap = cls.tinh_do_phuc_tap_anh(im)
            hist_info = cls.phan_tich_histogram(im)

        except Exception as e:
            print(f"[Cảnh báo] Lỗi la_anh_noi_dung quá trình tính toán tính năng: {e}")
            return False

        diem = 0

        if entropy >= 5.0:
            diem += 3
        elif entropy >= 4.0:
            diem += 2
        elif entropy >= 3.0:
            diem += 1

        if so_mau >= 1000:
            diem += 3
        elif so_mau >= 200:
            diem += 2
        elif so_mau >= 50:
            diem += 1

        if do_phuc_tap['edge_mean'] >= 20:
            diem += 2
        elif do_phuc_tap['edge_mean'] >= 10:
            diem += 1

        if do_phuc_tap['variance'] >= 2000:
            diem += 2
        elif do_phuc_tap['variance'] >= 500:
            diem += 1

        if hist_info['num_peaks'] >= 5:
            diem += 1
        if hist_info['dominant_ratio'] < 0.5:
            diem += 1

        return diem >= 4

    # LỌC ẢNH TRANG TRÍ (dựa trên metadata + context)

    @staticmethod
    def la_anh_trang_tri(kich_thuoc_anh, doan_van,
                          da_qua_phan_noi_dung: bool,
                          dem_paragraph_thuc: int,
                          tong_so_phan_tu: int,
                          vi_tri_hien_tai: int,
                          kich_thuoc_anh_da_xem: list) -> bool:
        # Bỏ qua lọc ảnh trang trí: báo cáo khoa học ít khi có ảnh trang trí,
        # và việc lọc thường loại nhầm các sơ đồ/biểu đồ đơn giản.
        return False
