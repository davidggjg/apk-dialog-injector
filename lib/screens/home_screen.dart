import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/github_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _titleController = TextEditingController();
  final _messageController = TextEditingController();
  final _button1Controller = TextEditingController();
  final _button2Controller = TextEditingController();
  final _button3Controller = TextEditingController();

  String? _selectedApkPath;
  String _selectedApkName = 'לא נבחר קובץ';
  String _log = 'ממתין לפעולה...';
  bool _isLoading = false;

  final _githubService = GitHubService();

  void _log_(String msg) {
    setState(() => _log = '$_log\n$msg');
  }

  Future<void> _pickApk() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['apk'],
    );
    if (result != null) {
      setState(() {
        _selectedApkPath = result.files.single.path;
        _selectedApkName = result.files.single.name;
      });
      _log_('✓ נבחר: $_selectedApkName');
    }
  }

  Future<void> _runAction(String mode) async {
    if (_selectedApkPath == null) {
      _showSnack('בחר APK קודם!');
      return;
    }
    if (mode == 'inject' && _titleController.text.isEmpty) {
      _showSnack('הכנס כותרת!');
      return;
    }

    setState(() {
      _isLoading = true;
      _log = 'מתחיל...';
    });

    try {
      _log_('מעדכן הגדרות...');
      await _githubService.updateConfig({
        'title': _titleController.text,
        'message': _messageController.text,
        'button1': _button1Controller.text,
        'button2': _button2Controller.text,
        'button3': _button3Controller.text,
      });

      _log_('מעלה APK...');
      await _githubService.uploadApk(File(_selectedApkPath!));

      _log_('מפעיל GitHub Action...');
      await _githubService.triggerAction(mode);

      _log_('ממתין לסיום (30 שניות)...');
      await Future.delayed(const Duration(seconds: 30));

      _log_('מוריד תוצאה...');
      final dir = await getTemporaryDirectory();
      final file = await _githubService.downloadResult(dir.path);

      _log_('✓ הושלם! מתקין...');
      await _installApk(file);

    } catch (e) {
      _log_('✗ שגיאה: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _installApk(File apkFile) async {
    // TODO: install apk
    _showSnack('APK מוכן: ${apkFile.path}');
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('APK Patcher'),
        backgroundColor: const Color(0xFF1A237E),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _pickApk,
                icon: const Icon(Icons.folder_open),
                label: const Text('בחר APK'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF3F51B5),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
            Center(
              child: Text(_selectedApkName,
                  style: const TextStyle(color: Colors.grey)),
            ),
            const SizedBox(height: 16),
            _buildField('כותרת הדיאלוג', 'הכנס כותרת...', _titleController),
            _buildField('תיאור הדיאלוג', 'הכנס תיאור...', _messageController,
                maxLines: 3),
            _buildField('שם כפתור 1', 'כפתור 1...', _button1Controller),
            _buildField('שם כפתור 2', 'כפתור 2...', _button2Controller),
            _buildField('שם כפתור 3', 'כפתור 3...', _button3Controller),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : () => _runAction('inject'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('הזרק דיאלוג',
                        style: TextStyle(fontSize: 16)),
              ),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : () => _runAction('remove'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: const Text('מחק דיאלוג',
                    style: TextStyle(fontSize: 16)),
              ),
            ),
            const SizedBox(height: 16),
            const Text('לוג:',
                style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black87,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _log,
                style: const TextStyle(
                    color: Colors.white, fontFamily: 'monospace'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildField(String label, String hint,
      TextEditingController controller, {int maxLines = 1}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        TextField(
          controller: controller,
          maxLines: maxLines,
          decoration: InputDecoration(
            hintText: hint,
            border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8)),
            contentPadding: const EdgeInsets.all(10),
          ),
        ),
        const SizedBox(height: 12),
      ],
    );
  }
