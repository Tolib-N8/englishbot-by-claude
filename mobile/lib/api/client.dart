import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

/// HTTP client for the FastAPI backend. Base URL is supplied per call so it
/// always reflects the latest setting.
class ApiClient {
  final String baseUrl;
  ApiClient(this.baseUrl);

  Uri _u(String path) => Uri.parse('$baseUrl$path');

  Future<dynamic> _get(String path) async {
    final res = await http.get(_u(path)).timeout(const Duration(seconds: 30));
    if (res.statusCode >= 400) {
      throw ApiException('HTTP ${res.statusCode}');
    }
    return jsonDecode(utf8.decode(res.bodyBytes));
  }

  Future<dynamic> _post(String path, [Map<String, dynamic>? body]) async {
    final res = await http
        .post(_u(path),
            headers: {'content-type': 'application/json'},
            body: jsonEncode(body ?? {}))
        .timeout(const Duration(seconds: 200));
    if (res.statusCode >= 400) {
      throw ApiException('HTTP ${res.statusCode}');
    }
    return jsonDecode(utf8.decode(res.bodyBytes));
  }

  Future<dynamic> _patch(String path, Map<String, dynamic> body) async {
    final res = await http
        .patch(_u(path),
            headers: {'content-type': 'application/json'},
            body: jsonEncode(body))
        .timeout(const Duration(seconds: 30));
    if (res.statusCode >= 400) {
      throw ApiException('HTTP ${res.statusCode}');
    }
    return jsonDecode(utf8.decode(res.bodyBytes));
  }

  // --- Health ---
  Future<bool> health() async {
    try {
      final res = await http.get(_u('/healthz')).timeout(const Duration(seconds: 8));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // --- Level ---
  Future<Level> getLevel() async => Level.fromJson(await _get('/api/v1/level'));
  Future<Level> assessLevel() async => Level.fromJson(await _post('/api/v1/level/assess'));
  Future<Level> setTarget(String band) async =>
      Level.fromJson(await _patch('/api/v1/level/target', {'target_band': band}));

  // --- Flashcards ---
  Future<FlashcardStats> flashcardStats() async =>
      FlashcardStats.fromJson(await _get('/api/v1/flashcards/stats'));

  Future<List<Flashcard>> dueCards({int limit = 50}) async {
    final data = await _get('/api/v1/flashcards/due?limit=$limit') as List;
    return data.map((e) => Flashcard.fromJson(e)).toList();
  }

  Future<void> review(int cardId, int quality) async {
    await _post('/api/v1/flashcards/$cardId/review', {'quality': quality});
  }

  // --- Conversations ---
  Future<List<Conversation>> conversations() async {
    final data = await _get('/api/v1/conversations') as List;
    return data.map((e) => Conversation.fromJson(e)).toList();
  }

  Future<Conversation> createConversation() async =>
      Conversation.fromJson(await _post('/api/v1/conversations', {}));

  Future<List<Message>> messages(int convId) async {
    final data = await _get('/api/v1/conversations/$convId') as Map<String, dynamic>;
    final msgs = data['messages'] as List? ?? [];
    return msgs.map((e) => Message.fromJson(e)).toList();
  }

  Future<void> summarizeSession(int convId) async {
    await _post('/api/v1/notes/summarize/$convId');
  }

  /// Stream the tutor reply as server-sent events.
  Stream<ChatEvent> chatStream(int convId, String content) async* {
    final req = http.Request('POST', _u('/api/v1/chat/stream'))
      ..headers['content-type'] = 'application/json'
      ..headers['accept'] = 'text/event-stream'
      ..body = jsonEncode({'conversation_id': convId, 'content': content});

    final res = await http.Client().send(req);
    if (res.statusCode >= 400) {
      yield ChatEvent('error', {'detail': 'HTTP ${res.statusCode}'});
      return;
    }

    var event = 'message';
    final dataLines = <String>[];

    Stream<String> lines = res.stream.transform(utf8.decoder).transform(const LineSplitter());
    await for (final line in lines) {
      if (line.isEmpty) {
        // dispatch
        if (dataLines.isNotEmpty) {
          final raw = dataLines.join('\n');
          dataLines.clear();
          try {
            final parsed = jsonDecode(raw) as Map<String, dynamic>;
            yield ChatEvent(event, parsed);
          } catch (_) {}
        }
        event = 'message';
        continue;
      }
      if (line.startsWith('event:')) {
        event = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.add(line.substring(5).trim());
      }
    }
  }

  // --- Exercises ---
  Future<List<TopicSuggestion>> exerciseTopics() async {
    final data = await _get('/api/v1/exercises/topics') as List;
    return data.map((e) => TopicSuggestion.fromJson(e)).toList();
  }

  Future<List<Exercise>> generateExercises(String topic, int count) async {
    final data = await _post('/api/v1/exercises/generate', {'topic': topic, 'count': count}) as List;
    return data.map((e) => Exercise.fromJson(e)).toList();
  }

  Future<AttemptResult> attempt(int exerciseId, String answer) async =>
      AttemptResult.fromJson(
          await _post('/api/v1/exercises/$exerciseId/attempt', {'user_answer': answer}));

  // --- Pronunciation ---
  Future<String> practicePhrase() async {
    final data = await _get('/api/v1/pronounce/practice') as Map<String, dynamic>;
    return data['phrase'] ?? '';
  }

  Future<PronunciationResult> uploadPronunciation(String audioPath, String targetText) async {
    final req = http.MultipartRequest('POST', _u('/api/v1/pronounce/transcribe'))
      ..fields['target_text'] = targetText
      ..files.add(await http.MultipartFile.fromPath('audio', audioPath));
    final res = await http.Response.fromStream(await req.send().timeout(const Duration(seconds: 300)));
    if (res.statusCode >= 400) {
      throw ApiException('HTTP ${res.statusCode}');
    }
    return PronunciationResult.fromJson(jsonDecode(utf8.decode(res.bodyBytes)));
  }
}
