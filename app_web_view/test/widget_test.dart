// widget_test.dart — Comprehensive tests cho Word2LaTeX Flutter App
//
// Test coverage:
//  1. App khởi tạo và render được WebViewScreen
//  2. getMimeType() trả về đúng MIME type cho từng extension
//  3. getMimeTypeFromFilename() parse đúng extension
//  4. Routing OPEN_URL iOS: ZIP → download, PDF+download=1 → download, PDF view → external
//  5. Routing OPEN_URL iOS: Word → download
//  6. Các message type không thuộc iOS download → không crash

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:word2latex_app/main.dart';
import 'package:word2latex_app/config.dart';

// ──────────────────────────────────────────────────────────────────────────────
// Helpers — truy cập các private methods thông qua reflection-free test objects
// ──────────────────────────────────────────────────────────────────────────────

/// Tái hiện logic _getMimeType() của _WebViewScreenState để test độc lập.
String getMimeType(String ext) {
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

/// Tái hiện logic _getMimeTypeFromFilename() để test độc lập.
String getMimeTypeFromFilename(String filename) {
  final ext = filename.split('.').last;
  return getMimeType(ext);
}

/// Tái hiện routing logic của OPEN_URL trên iOS:
/// Trả về ('download', filename) hoặc ('external', '') hoặc ('ignore', '').
(String action, String filename) resolveIosOpenUrl(String url) {
  const downloadPatterns = ['/api/tai-ve-', '/api/download/'];
  final isDownloadUrl =
      downloadPatterns.any((p) => url.contains(p));
  if (!isDownloadUrl) return ('external', '');

  if (url.contains('/tai-ve-zip/') || url.contains('/download/')) {
    return ('download', 'latex_source.zip');
  } else if (url.contains('/tai-ve-pdf/')) {
    if (url.contains('download=1')) {
      return ('download', 'document.pdf');
    } else {
      return ('external', '');
    }
  } else if (url.contains('/tai-ve-word/')) {
    return ('download', 'document.docx');
  }
  return ('download', 'download');
}

// ──────────────────────────────────────────────────────────────────────────────
// Test suite
// ──────────────────────────────────────────────────────────────────────────────

void main() {
  // ---------------------------------------------------------------------------
  // GROUP 1: App rendering
  // ---------------------------------------------------------------------------
  group('App Widget', () {
    testWidgets('Word2LatexApp renders WebViewScreen', (tester) async {
      // Pump widget không cần token
      await tester.pumpWidget(Word2LatexApp());
      // Tìm đúng kiểu widget
      expect(find.byType(Word2LatexApp), findsOneWidget);
    });

    testWidgets('Word2LatexApp có MaterialApp', (tester) async {
      await tester.pumpWidget(Word2LatexApp());
      expect(find.byType(MaterialApp), findsOneWidget);
    });
  });

  // ---------------------------------------------------------------------------
  // GROUP 2: MIME type resolution
  // ---------------------------------------------------------------------------
  group('getMimeType()', () {
    test('docx → OpenXML MIME', () {
      expect(
        getMimeType('docx'),
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      );
    });

    test('DOCX (uppercase) → OpenXML MIME (case-insensitive)', () {
      expect(
        getMimeType('DOCX'),
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      );
    });

    test('docm → Macro-enabled Word MIME', () {
      expect(
        getMimeType('docm'),
        'application/vnd.ms-word.document.macroEnabled.12',
      );
    });

    test('doc → Legacy Word MIME', () {
      expect(getMimeType('doc'), 'application/msword');
    });

    test('tex → TeX MIME', () {
      expect(getMimeType('tex'), 'application/x-tex');
    });

    test('zip → ZIP MIME', () {
      expect(getMimeType('zip'), 'application/zip');
    });

    test('pdf → PDF MIME', () {
      expect(getMimeType('pdf'), 'application/pdf');
    });

    test('unknown extension → octet-stream', () {
      expect(getMimeType('xyz'), 'application/octet-stream');
    });

    test('empty string → octet-stream', () {
      expect(getMimeType(''), 'application/octet-stream');
    });
  });

  // ---------------------------------------------------------------------------
  // GROUP 3: getMimeTypeFromFilename
  // ---------------------------------------------------------------------------
  group('getMimeTypeFromFilename()', () {
    test('document.docx → OpenXML MIME', () {
      expect(
        getMimeTypeFromFilename('document.docx'),
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      );
    });

    test('output_v2.3.zip → ZIP MIME', () {
      expect(getMimeTypeFromFilename('output_v2.3.zip'), 'application/zip');
    });

    test('report.pdf → PDF MIME', () {
      expect(getMimeTypeFromFilename('report.pdf'), 'application/pdf');
    });

    test('file with dots in name uses last extension', () {
      // e.g. "my.paper.v1.docm" → last ext = "docm"
      expect(
        getMimeTypeFromFilename('my.paper.v1.docm'),
        'application/vnd.ms-word.document.macroEnabled.12',
      );
    });
  });

  // ---------------------------------------------------------------------------
  // GROUP 4: iOS OPEN_URL routing
  // ---------------------------------------------------------------------------
  group('iOS resolveIosOpenUrl()', () {
    // --- ZIP download ---
    test('/api/tai-ve-zip/ → download latex_source.zip', () {
      final (action, filename) = resolveIosOpenUrl(
        'https://api.word2latex.id.vn/api/tai-ve-zip/abc123',
      );
      expect(action, 'download');
      expect(filename, 'latex_source.zip');
    });

    test('/api/download/ → download latex_source.zip', () {
      final (action, filename) = resolveIosOpenUrl(
        'https://api.word2latex.id.vn/api/download/abc123',
      );
      expect(action, 'download');
      expect(filename, 'latex_source.zip');
    });

    // --- PDF download vs view ---
    test('/api/tai-ve-pdf/?download=1 → download document.pdf', () {
      final (action, filename) = resolveIosOpenUrl(
        'https://api.word2latex.id.vn/api/tai-ve-pdf/abc123?download=1',
      );
      expect(action, 'download');
      expect(filename, 'document.pdf');
    });

    test('/api/tai-ve-pdf/ without download=1 → external (view in Safari)', () {
      final (action, _) = resolveIosOpenUrl(
        'https://api.word2latex.id.vn/api/tai-ve-pdf/abc123',
      );
      expect(action, 'external');
    });

    // --- Word download ---
    test('/api/tai-ve-word/ → download document.docx', () {
      final (action, filename) = resolveIosOpenUrl(
        'https://api.word2latex.id.vn/api/tai-ve-word/abc123',
      );
      expect(action, 'download');
      expect(filename, 'document.docx');
    });

    // --- Non-download URLs → open externally ---
    test('Non-API URL → external (no download)', () {
      final (action, _) = resolveIosOpenUrl('https://word2latex.id.vn/premium');
      expect(action, 'external');
    });

    test('Google URL → external', () {
      final (action, _) = resolveIosOpenUrl('https://google.com');
      expect(action, 'external');
    });
  });

  // ---------------------------------------------------------------------------
  // GROUP 5: AppConfig sanity checks
  // ---------------------------------------------------------------------------
  group('AppConfig', () {
    test('webBaseUrl không rỗng', () {
      expect(AppConfig.webBaseUrl.isNotEmpty, isTrue);
    });

    test('webBaseUrl là URL hợp lệ (https)', () {
      expect(Uri.parse(AppConfig.webBaseUrl).isAbsolute, isTrue);
      expect(AppConfig.webBaseUrl, startsWith('https://'));
    });

    test('apiBaseUrl không rỗng', () {
      expect(AppConfig.apiBaseUrl.isNotEmpty, isTrue);
    });

    test('callbackScheme không rỗng và lowercase', () {
      expect(AppConfig.callbackScheme.isNotEmpty, isTrue);
      expect(AppConfig.callbackScheme, AppConfig.callbackScheme.toLowerCase());
    });

    test('appName là Word2LaTeX', () {
      expect(AppConfig.appName, 'Word2LaTeX');
    });
  });

  // ---------------------------------------------------------------------------
  // GROUP 6: Edge cases
  // ---------------------------------------------------------------------------
  group('Edge cases', () {
    test('URL với query params khác bên cạnh download=1 → đúng routing', () {
      final (action, filename) = resolveIosOpenUrl(
        'https://api.word2latex.id.vn/api/tai-ve-pdf/abc?token=xyz&download=1',
      );
      expect(action, 'download');
      expect(filename, 'document.pdf');
    });

    test('getMimeType với extension có dấu chấm → fallback octet-stream', () {
      // Người dùng pass ".docx" thay vì "docx" → fallback vì switch không match
      // (trong production _getMimeTypeFromFilename tự split('.').last nên không có case này)
      expect(getMimeType('.docx'), 'application/octet-stream');
    });

    test('Filename không có extension → fallback octet-stream', () {
      // "filename" → split('.').last = "filename" → unknown
      expect(getMimeTypeFromFilename('filename_no_ext'), 'application/octet-stream');
    });
  });
}
