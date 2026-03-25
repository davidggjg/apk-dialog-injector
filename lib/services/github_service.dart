import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class GitHubService {
  Future<Map<String, String>> _getSettings() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'token': prefs.getString('github_token') ?? '',
      'username': prefs.getString('github_username') ?? '',
      'repo': prefs.getString('github_repo') ?? '',
    };
  }

  Future<String> _baseUrl() async {
    final s = await _getSettings();
    return 'https://api.github.com/repos/${s['username']}/${s['repo']}';
  }

  Future<Map<String, String>> _headers() async {
    final s = await _getSettings();
    return {
      'Authorization': 'token ${s['token']}',
      'Accept': 'application/vnd.github.v3+json',
      'Content-Type': 'application/json',
    };
  }

  Future<void> updateConfig(Map<String, String> config) async {
    final base = await _baseUrl();
    final headers = await _headers();
    final content = base64Encode(utf8.encode(jsonEncode(config)));
    final sha = await _getFileSha('config.json');

    final body = <String, dynamic>{
      'message': 'update config',
      'content': content,
    };
    if (sha != null) body['sha'] = sha;

    final response = await http.put(
      Uri.parse('$base/contents/config.json'),
      headers: headers,
      body: jsonEncode(body),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('שגיאה בעדכון config: ${response.statusCode}');
    }
  }

  Future<void> uploadApk(File apkFile) async {
    final base = await _baseUrl();
    final headers = await _headers();
    final bytes = await apkFile.readAsBytes();
    final content = base64Encode(bytes);
    final sha = await _getFileSha('input/input.apk');

    final body = <String, dynamic>{
      'message': 'upload apk',
      'content': content,
    };
    if (sha != null) body['sha'] = sha;

    final response = await http.put(
      Uri.parse('$base/contents/input/input.apk'),
      headers: headers,
      body: jsonEncode(body),
    );
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('שגיאה בהעלאת APK: ${response.statusCode}');
    }
  }

  Future<void> triggerAction(String mode) async {
    final base = await _baseUrl();
    final headers = await _headers();

    final response = await http.post(
      Uri.parse('$base/actions/workflows/patch.yml/dispatches'),
      headers: headers,
      body: jsonEncode({'ref': 'main', 'inputs': {'mode': mode}}),
    );
    if (response.statusCode != 204) {
      throw Exception('שגיאה בהפעלת Action: ${response.statusCode}');
    }
  }

  Future<String?> _getFileSha(String path) async {
    try {
      final base = await _baseUrl();
      final headers = await _headers();
      final response = await http.get(
        Uri.parse('$base/contents/$path'),
        headers: headers,
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body)['sha'];
      }
    } catch (_) {}
    return null;
  }

  Future<File> downloadResult(String cacheDir) async {
    final base = await _baseUrl();
    final headers = await _headers();

    await Future.delayed(const Duration(seconds: 5));

    final runsResponse = await http.get(
      Uri.parse('$base/actions/runs?status=completed&per_page=1'),
      headers: headers,
    );
    final runs = jsonDecode(runsResponse.body);
    final runId = runs['workflow_runs'][0]['id'];

    final artsResponse = await http.get(
      Uri.parse('$base/actions/runs/$runId/artifacts'),
      headers: headers,
    );
    final arts = jsonDecode(artsResponse.body);
    final downloadUrl = arts['artifacts'][0]['archive_download_url'];

    final dlResponse = await http.get(
      Uri.parse(downloadUrl),
      headers: headers,
    );

    final file = File('$cacheDir/patched_signed.apk');
    await file.writeAsBytes(dlResponse.bodyBytes);
    return file;
  }
}
