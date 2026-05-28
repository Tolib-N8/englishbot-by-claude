import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Holds the backend base URL (e.g. a Tailscale address) and persists it.
class SettingsModel extends ChangeNotifier {
  static const _key = 'backend_base_url';
  static const defaultUrl = 'http://100.64.0.1:8000';

  String _baseUrl = defaultUrl;
  bool _loaded = false;

  String get baseUrl => _baseUrl;
  bool get loaded => _loaded;

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_key) ?? defaultUrl;
    _loaded = true;
    notifyListeners();
  }

  Future<void> setBaseUrl(String url) async {
    _baseUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, _baseUrl);
    notifyListeners();
  }
}
