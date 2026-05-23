import 'dart:io';
import 'dart:math';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:webview_flutter_wkwebview/webview_flutter_wkwebview.dart';
import 'package:flutter_web_auth_2/flutter_web_auth_2.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:file_picker/file_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:share_plus/share_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Thiết lập giao diện hệ thống (Status Bar)
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      statusBarBrightness: Brightness.dark, // Cho iOS
    ),
  );

  // Lấy token đã lưu (nếu có)
  final prefs = await SharedPreferences.getInstance();
  final token = prefs.getString('access_token');

  runApp(Word2LatexApp(initialToken: token));
}

class Word2LatexApp extends StatelessWidget {
  final String? initialToken;

  static final List<Color> _brandColors = [
    const Color(0xFF7C3AED), // Primary purple
    const Color(0xFF6D28D9),
    const Color(0xFF5B21B6),
    const Color(0xFF4C1D95),
  ];

  Word2LatexApp({super.key, this.initialToken});

  final Color _primaryColor =
      _brandColors[Random().nextInt(_brandColors.length)];

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: _primaryColor),
        useMaterial3: true,
      ),
      home: WebViewScreen(token: initialToken),
    );
  }
}

// ============================================================
// MAIN WEBVIEW SCREEN
// ============================================================
class WebViewScreen extends StatefulWidget {
  final String? token;
  const WebViewScreen({super.key, required this.token});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  bool _hasError = false;
  double _loadingProgress = 0;
  String? _activeToken;
  bool _isAuthenticating = false;

  @override
  void initState() {
    super.initState();
    _activeToken = widget.token;
    _initWebView();
  }

  // --- WebView Initialization ---

  Future<void> _initWebView() async {
    // ===== iOS WKWebView Configuration =====
    WebViewController controller;

    if (Platform.isIOS) {
      final WebKitWebViewControllerCreationParams params =
          WebKitWebViewControllerCreationParams(
        allowsInlineMediaPlayback: true,
        mediaTypesRequiringUserAction: const <PlaybackMediaTypes>{},
      );
      controller = WebViewController.fromPlatformCreationParams(params);

      // Disable iOS scroll bounce & configure WKWebView
      final webKitController =
          controller.platform as WebKitWebViewController;
      await webKitController.setAllowsBackForwardNavigationGestures(true);

    } else {
      controller = WebViewController();
    }

    _controller = controller
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF070513))
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (progress) =>
              setState(() => _loadingProgress = progress / 100),
          onPageStarted: (_) =>
              setState(() {
                _isLoading = true;
                _hasError = false;
              }),
          onPageFinished: (String url) async {
            setState(() {
              _isLoading = false;
            });
            // Inject Safe Area Top padding from Flutter to CSS variable
            final double statusBarHeight =
                MediaQuery.of(context).padding.top;
            await _controller.runJavaScript(
                "document.documentElement.style.setProperty('--safe-area-top', '${statusBarHeight}px')");

            if (_activeToken != null) _injectTokenToWeb(_activeToken!);

            // iOS: Inject JS để handle file upload & download qua FlutterBridge
            if (Platform.isIOS) {
              await _injectIOSBridgeScript();
            }
          },
          onWebResourceError: (_) =>
              setState(() {
                _isLoading = false;
                _hasError = true;
              }),
          onNavigationRequest: _handleNavigation,
        ),
      )
      ..addJavaScriptChannel(
        'FlutterBridge',
        onMessageReceived: _handleWebMessage,
      );

    await _setupAppCookie();

    // ===== Android: file selector hook =====
    if (_controller.platform is AndroidWebViewController) {
      (_controller.platform as AndroidWebViewController).setOnShowFileSelector(
        (FileSelectorParams params) async {
          try {
            final result = await FilePicker.pickFiles(
              type: FileType.custom,
              allowedExtensions: ['doc', 'docx', 'docm', 'tex', 'zip'],
              allowMultiple: params.mode == FileSelectorMode.openMultiple,
            );

            if (result != null && result.files.isNotEmpty) {
              return result.files
                  .where((file) => file.path != null)
                  .map((file) => Uri.file(file.path!).toString())
                  .toList();
            }
          } catch (e) {
            debugPrint('==> Lỗi khi chọn file Android: $e');
          }
          return [];
        },
      );
    }

    _loadAppUrl(_activeToken);
  }

  /// Inject JavaScript bridge script cho iOS để:
  /// 1. Handle file upload input[type=file] → gọi FlutterBridge
  /// 2. Handle download link → gọi FlutterBridge thay vì blob URL
  Future<void> _injectIOSBridgeScript() async {
    await _controller.runJavaScript(r'''
      (function() {
        // --- 1. iOS File Upload: intercept <input type="file"> clicks ---
        // WKWebView on iOS supports native document picker natively via file input,
        // but we add a FlutterBridge fallback for programmatic triggers.
        document.addEventListener('click', function(e) {
          var el = e.target;
          // Walk up to find file input
          while (el && el.tagName !== 'INPUT') el = el.parentElement;
          if (el && el.type === 'file') {
            // Allow native WKWebView file picker to handle it (it works on iOS 14+)
            return;
          }
        }, true);

        // --- 2. iOS Download: intercept download anchor clicks ---
        document.addEventListener('click', function(e) {
          var el = e.target;
          // Walk up DOM to find anchor tag
          while (el && el.tagName !== 'A') el = el.parentElement;
          if (!el) return;

          var href = el.getAttribute('href') || '';
          var download = el.getAttribute('download');
          var isDownload = download !== null;

          if (isDownload && href) {
            e.preventDefault();
            e.stopPropagation();
            // Send to Flutter to handle download via share sheet
            window.FlutterBridge.postMessage(JSON.stringify({
              type: 'IOS_DOWNLOAD',
              url: href.startsWith('http') ? href : window.location.origin + href,
              filename: download || 'download'
            }));
          }
        }, true);

        // --- 3. iOS PDF View: intercept PDF open requests ---
        // If the web opens a PDF URL via window.open(), intercept and send to Flutter
        var originalOpen = window.open;
        window.open = function(url, target, features) {
          if (url && (url.includes('/download/') || url.includes('/pdf/') || url.endsWith('.pdf'))) {
            window.FlutterBridge.postMessage(JSON.stringify({
              type: 'IOS_OPEN_URL',
              url: url.startsWith('http') ? url : window.location.origin + url
            }));
            return null;
          }
          return originalOpen.call(this, url, target, features);
        };

        console.log('[Flutter iOS Bridge] Injected successfully');
      })();
    ''');
  }

  // --- Helper Methods ---

  /// Thiết lập cookie định danh để Web nhận biết môi trường App
  Future<void> _setupAppCookie() async {
    final domain = Uri.parse(AppConfig.webBaseUrl).host;
    await WebViewCookieManager().setCookie(
      WebViewCookie(
          name: 'viewappmobie', value: 'true', domain: domain, path: '/'),
    );
  }

  /// Load trang web chính với token (nếu có)
  void _loadAppUrl(String? token) {
    final url = token != null
        ? '${AppConfig.webBaseUrl}/?token=$token'
        : AppConfig.webBaseUrl;
    _controller.loadRequest(Uri.parse(url));
  }

  /// Chặn các điều hướng không hợp lệ
  NavigationDecision _handleNavigation(NavigationRequest request) {
    final url = request.url;

    // ✅ Cho phép các URL chứa callback hoặc token đi qua bình thường
    if (url.contains('callback') || url.contains('token=')) {
      return NavigationDecision.navigate;
    }

    if (url.startsWith(AppConfig.webBaseUrl)) {
      return NavigationDecision.navigate;
    }
    debugPrint('==> Đã chặn điều hướng ngoài: ${request.url}');
    return NavigationDecision.prevent;
  }

  /// Xử lý các thông điệp gửi từ JavaScript
  void _handleWebMessage(JavaScriptMessage message) async {
    final data = message.message;
    debugPrint('==> Bridge received: $data');

    if (data.startsWith('{')) {
      try {
        final Map<String, dynamic> msg = jsonDecode(data);

        // iOS Download: tải file và mở Share Sheet
        if (msg['type'] == 'IOS_DOWNLOAD') {
          final String fileUrl = msg['url'];
          final String filename = msg['filename'] ?? 'download';
          await _handleIOSDownload(fileUrl, filename);
          return;
        }

        // iOS Open URL (PDF viewer, external link)
        if (msg['type'] == 'IOS_OPEN_URL') {
          final String url = msg['url'];
          await _openUrlExternally(url);
          return;
        }

        // Flutter-native open external URL
        if (msg['type'] == 'OPEN_URL') {
          final String url = msg['url'];
          await _openUrlExternally(url);
          return;
        }

        // iOS file picker request từ JavaScript
        if (msg['type'] == 'IOS_FILE_PICK') {
          await _handleIOSFilePick(msg);
          return;
        }
      } catch (e) {
        debugPrint('==> Lỗi parse message JSON: $e');
      }
    }

    switch (data) {
      case 'LOGOUT':
        _processLogout();
        break;
      default:
        if (data.startsWith('GOOGLE_LOGIN:')) {
          final sessionId = data.split(':')[1];
          _triggerNativeGoogleLogin(sessionId);
        } else if (data.startsWith('SAVE_TOKEN:')) {
          final token = data.split(':')[1];
          _saveToken(token);
        }
        break;
    }
  }

  /// iOS: Mở URL trong browser ngoài
  Future<void> _openUrlExternally(String url) async {
    final Uri uri = Uri.parse(url);
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('==> Không thể mở URL: $e');
    }
  }

  /// iOS: Tải file từ URL và mở Share Sheet để save về máy
  Future<void> _handleIOSDownload(String fileUrl, String filename) async {
    debugPrint('==> [iOS Download] Bắt đầu tải: $fileUrl');

    // Thêm auth header nếu có token
    final Map<String, String> headers = {
      'Accept': '*/*',
    };
    if (_activeToken != null) {
      headers['Authorization'] = 'Bearer $_activeToken';
    }

    try {
      // Hiện thông báo đang tải
      await _controller.runJavaScript(
          "window.dispatchEvent(new CustomEvent('flutter_download_start', {detail: {filename: '$filename'}}))");

      final response = await http.get(Uri.parse(fileUrl), headers: headers);
      if (response.statusCode != 200) {
        debugPrint('==> [iOS Download] Lỗi HTTP: ${response.statusCode}');
        await _controller.runJavaScript(
            "window.dispatchEvent(new CustomEvent('flutter_download_error', {detail: {message: 'HTTP ${response.statusCode}'}}))");
        return;
      }

      // Lưu vào temp directory
      final tempDir = await getTemporaryDirectory();
      final file = File('${tempDir.path}/$filename');
      await file.writeAsBytes(response.bodyBytes);

      // Mở iOS Share Sheet (share_plus v10 API)
      await Share.shareXFiles(
        [XFile(file.path, name: filename, mimeType: _getMimeTypeFromFilename(filename))],
        subject: 'Word2LaTeX — $filename',
      );

      await _controller.runJavaScript(
          "window.dispatchEvent(new CustomEvent('flutter_download_done', {detail: {filename: '$filename'}}))");
      debugPrint('==> [iOS Download] Hoàn tất: $filename');
    } catch (e) {
      debugPrint('==> [iOS Download] Lỗi: $e');
      await _controller.runJavaScript(
          "window.dispatchEvent(new CustomEvent('flutter_download_error', {detail: {message: '${e.toString().replaceAll("'", "\\'")}'"
          "}}))");
    }
  }

  /// iOS: File picker request từ JavaScript (programmatic trigger)
  Future<void> _handleIOSFilePick(Map<String, dynamic> msg) async {
    try {
      final result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['doc', 'docx', 'docm', 'tex', 'zip'],
        allowMultiple: false,
      );

      if (result != null && result.files.isNotEmpty) {
        final file = result.files.first;
        if (file.path != null) {
          // Đọc file bytes
          final bytes = await File(file.path!).readAsBytes();
          final base64Data = base64Encode(bytes);
          final mimeType = _getMimeType(file.extension ?? '');

          // Inject file vào web dưới dạng base64 + dispatch CustomEvent
          await _controller.runJavaScript('''
            (function() {
              try {
                var byteString = atob('$base64Data');
                var ab = new ArrayBuffer(byteString.length);
                var ia = new Uint8Array(ab);
                for (var i = 0; i < byteString.length; i++) { ia[i] = byteString.charCodeAt(i); }
                var blob = new Blob([ab], {type: '$mimeType'});
                var file = new File([blob], '${file.name}', {type: '$mimeType'});
                window.dispatchEvent(new CustomEvent('flutter_file_picked', {detail: {file: file, name: '${file.name}'}}));
                console.log('[Flutter iOS] File injected: ${file.name}');
              } catch(e) {
                console.error('[Flutter iOS] File inject error:', e);
              }
            })();
          ''');
        }
      }
    } catch (e) {
      debugPrint('==> [iOS FilePick] Lỗi: $e');
    }
  }

  String _getMimeType(String ext) {
    switch (ext.toLowerCase()) {
      case 'docx':
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      case 'docm':
        return 'application/vnd.ms-word.document.macroEnabled.12';
      case 'doc':
        return 'application/msword';
      case 'tex':
        return 'application/x-tex';
      case 'zip':
        return 'application/zip';
      case 'pdf':
        return 'application/pdf';
      default:
        return 'application/octet-stream';
    }
  }

  /// Lấy MIME type từ tên file đầy đủ (có extension)
  String _getMimeTypeFromFilename(String filename) {
    final ext = filename.split('.').last;
    return _getMimeType(ext);
  }

  // --- Core Logic ---

  int _cctOpenCount = 0;

  Future<void> _triggerNativeGoogleLogin(String sessionId) async {
    if (_isAuthenticating) return;
    _isAuthenticating = true;

    _cctOpenCount++;
    debugPrint(
        '==> 🚀 [Cloud-Sync] Mở Tab login cho Session: $sessionId - Lần: $_cctOpenCount');

    try {
      final loginUrl =
          '${AppConfig.apiBaseUrl}/auth/google/login/flutter?session_id=$sessionId&ngrok-skip-browser-warning=1';

      await FlutterWebAuth2.authenticate(
        url: loginUrl,
        callbackUrlScheme:
            AppConfig.callbackScheme, // word2latex:// - tự đóng CCT sau redirect
      );
    } catch (e) {
      debugPrint('==> [Cloud-Sync] CCT closed/cancelled: $e');
    } finally {
      _isAuthenticating = false;
    }
  }

  Future<void> _processLogout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');

    await WebViewCookieManager().clearCookies();
    await _setupAppCookie(); // Re-set mobile identifier after clear

    setState(() => _activeToken = null);
    _loadAppUrl(null);
  }

  Future<void> _saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
    setState(() => _activeToken = token);
  }

  Future<void> _injectTokenToWeb(String token) async {
    await _controller.runJavaScript('''
      try {
        localStorage.setItem('access_token', '$token');
        window.dispatchEvent(new CustomEvent('flutter_token_ready', { detail: { token: '$token' } }));
        console.log('[Flutter] Token injected');
      } catch(e) {}
    ''');
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    SystemChrome.setSystemUIOverlayStyle(
      SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness:
            isDark ? Brightness.light : Brightness.dark,
        statusBarBrightness: isDark ? Brightness.dark : Brightness.light,
      ),
    );

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        if (await _controller.canGoBack()) {
          _controller.goBack();
        } else if (context.mounted) {
          SystemNavigator.pop();
        }
      },
      child: Scaffold(
        // iOS: resizeToAvoidBottomInset=false agar keyboard không đẩy WebView
        resizeToAvoidBottomInset: false,
        backgroundColor: const Color(0xFF070513),
        body: Stack(
          children: [
            SafeArea(
              child: _hasError
                  ? _ErrorView(onRetry: () => _controller.reload())
                  : WebViewWidget(controller: _controller),
            ),
            if (_isLoading && !_hasError) _buildProgressBar(),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressBar() {
    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: LinearProgressIndicator(
        value: _loadingProgress,
        color: const Color(0xFF7C3AED), // Primary purple
        minHeight: 3,
      ),
    );
  }
}

// ============================================================
// ERROR VIEW - Hiển thị khi mất kết nối
// ============================================================
class _ErrorView extends StatelessWidget {
  final VoidCallback onRetry;
  const _ErrorView({required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.cloud_off_rounded,
              size: 80,
              color: colorScheme.primary.withValues(alpha: 0.6),
            ),
            const SizedBox(height: 24),
            Text(
              'Mất kết nối Internet',
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: colorScheme.onSurface,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Không thể tải nội dung. Vui lòng kiểm tra lại đường truyền và thử lại.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded),
              label: const Text('Thử lại'),
              style: ElevatedButton.styleFrom(
                backgroundColor: colorScheme.primary,
                foregroundColor: colorScheme.onPrimary,
                padding: const EdgeInsets.symmetric(
                    horizontal: 32, vertical: 15),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                elevation: 0,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
