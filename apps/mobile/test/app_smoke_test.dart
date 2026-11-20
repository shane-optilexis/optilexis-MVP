import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:optilexis_mobile/main.dart';
import 'package:optilexis_mobile/src/api_client.dart';
import 'package:optilexis_mobile/src/models.dart';

class FakeApi extends OptilexisApi {
  @override
  bool get debugTokenConfigured => true;
  @override
  Future<Map<String, dynamic>> health() async => {'status': 'ok', 'environment': 'development'};
  @override
  Future<List<JourneyDto>> listJourneys() async => [];
  @override
  void dispose() {}
}

class FakeNoAuthApi extends OptilexisApi {
  @override
  Future<Map<String, dynamic>> health() async => {'status': 'ok', 'environment': 'development'};
  @override
  void dispose() {}
}

void main() {
  testWidgets('renders branded setup for a verified debug identity', (tester) async {
    await tester.pumpWidget(OptilexisApp(api: FakeApi()));
    await tester.pumpAndSettle();
    expect(find.text('OPTILEXIS'), findsOneWidget);
    expect(find.text('Plan a journey'), findsOneWidget);
    expect(find.textContaining('DEVELOPMENT SIMULATOR'), findsOneWidget);
    expect(find.text('My journeys (persisted)'), findsOneWidget);
  });

  testWidgets('requires explicit development identity by default', (tester) async {
    await tester.pumpWidget(OptilexisApp(api: FakeNoAuthApi()));
    await tester.pumpAndSettle();
    expect(find.text('Development sign in'), findsOneWidget);
    expect(find.text('Plan a journey'), findsNothing);
    expect(find.byType(TextField), findsOneWidget);
  });
}
