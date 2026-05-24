/// Cấu hình ứng dụng Word2LaTeX Mobile
///
/// Chứa các URL kết nối tới Backend/Frontend.
/// Khi deploy production, thay đổi các URL phù hợp.
class AppConfig {
  /// Tên ứng dụng hiển thị
  static const String appName = 'Word2LaTeX';

  /// URL trang web chính (Frontend qua Ngrok hoặc domain thật)
  /// WebView sẽ load URL này.
  static const String webBaseUrl =
      'https://word2latex.id.vn';

  /// URL API Backend (qua Vite Proxy = cùng origin với webBaseUrl)
  /// Dùng cho các API call từ Flutter native (ví dụ: Google Login redirect).
  static const String apiBaseUrl =
      'https://api.word2latex.id.vn/api';

  /// Callback URL scheme để Chrome Custom Tab tự đóng sau khi đăng nhập
  static const String callbackScheme = 'word2latex';
}
