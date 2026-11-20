/// Validated API response models. There are no invented location or SDK events.
class JourneyConsent {
  const JourneyConsent({required this.location, required this.microphone, required this.camera});
  final bool location;
  final bool microphone;
  final bool camera;

  factory JourneyConsent.fromJson(Map<String, dynamic> json) => JourneyConsent(
    location: json['location'] == true,
    microphone: json['microphone'] == true,
    camera: json['camera'] == true,
  );
}

class JourneyDto {
  const JourneyDto({
    required this.id, required this.destination, required this.language,
    required this.mode, required this.navigationMode, required this.stage,
    required this.consent, required this.createdAt, this.closedAt,
  });
  final String id;
  final String destination;
  final String language;
  final String mode;
  final String navigationMode;
  final String stage;
  final JourneyConsent consent;
  final DateTime createdAt;
  final DateTime? closedAt;

  bool get active => closedAt == null;

  factory JourneyDto.fromJson(Map<String, dynamic> json) => JourneyDto(
    id: json['id'] as String,
    destination: json['destination'] as String,
    language: json['language'] as String,
    mode: json['mode'] as String,
    navigationMode: json['navigation_mode'] as String,
    stage: json['stage'] as String,
    consent: JourneyConsent.fromJson(json['consent'] as Map<String, dynamic>),
    createdAt: DateTime.parse(json['created_at'] as String),
    closedAt: json['closed_at'] == null ? null : DateTime.parse(json['closed_at'] as String),
  );
}

class RecommendationDto {
  const RecommendationDto({required this.title, required this.message, required this.action});
  final String title;
  final String message;
  final String action;

  factory RecommendationDto.fromJson(Map<String, dynamic> json) => RecommendationDto(
    title: json['title'] as String,
    message: json['message'] as String,
    action: json['action'] as String,
  );
}

class EventOutcomeDto {
  const EventOutcomeDto({required this.suppressed, required this.simulated, this.reason, this.suggestion});
  final bool suppressed;
  final bool simulated;
  final String? reason;
  final RecommendationDto? suggestion;

  factory EventOutcomeDto.fromJson(Map<String, dynamic> json) => EventOutcomeDto(
    suppressed: json['suppressed'] as bool,
    simulated: json['simulated'] as bool,
    reason: json['reason'] as String?,
    suggestion: json['suggestion'] == null ? null :
      RecommendationDto.fromJson(json['suggestion'] as Map<String, dynamic>),
  );
}

class PhraseDto {
  const PhraseDto({required this.sourceText, required this.translatedText, required this.audioAvailable});
  final String sourceText;
  final String translatedText;
  final bool audioAvailable;

  factory PhraseDto.fromJson(Map<String, dynamic> json) => PhraseDto(
    sourceText: json['source_text'] as String,
    translatedText: json['translated_text'] as String,
    audioAvailable: json['audio_available'] == true,
  );
}
