import 'package:flutter_test/flutter_test.dart';
import 'package:optilexis_mobile/src/models.dart';

void main() {
  test('empty consent response remains fully denied', () {
    final consent = JourneyConsent.fromJson({'location': false, 'camera': false, 'microphone': false});
    expect(consent.location, false);
    expect(consent.camera, false);
    expect(consent.microphone, false);
  });
}
