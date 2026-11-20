/// Permission-aware future speech interface. No microphone capture is implemented.
class SpeechUnavailable implements Exception {
  const SpeechUnavailable(this.message);
  final String message;
  @override
  String toString() => message;
}

class SpeechConsent {
  const SpeechConsent({required this.consentGranted, required this.osPermissionGranted,
    required this.userActivated});
  final bool consentGranted;
  final bool osPermissionGranted;
  final bool userActivated;

  void validate() {
    if (!consentGranted || !osPermissionGranted || !userActivated) {
      throw const SpeechUnavailable('Speech requires explicit action and OS permission');
    }
  }
}

abstract class SpeechTranslator {
  Future<String> recognize(List<int> encodedAudio, String locale, SpeechConsent consent);
  Future<String> translate(String text, String locale);
  Future<List<int>> synthesize(String text, String locale);
}

class UnconfiguredSpeechProvider implements SpeechTranslator {
  const UnconfiguredSpeechProvider();
  @override
  Future<String> recognize(List<int> encodedAudio, String locale, SpeechConsent consent) async {
    consent.validate();
    throw const SpeechUnavailable('No ASR provider configured');
  }
  @override
  Future<String> translate(String text, String locale) async =>
      throw const SpeechUnavailable('No live translation provider configured');
  @override
  Future<List<int>> synthesize(String text, String locale) async =>
      throw const SpeechUnavailable('No TTS provider configured');
}
