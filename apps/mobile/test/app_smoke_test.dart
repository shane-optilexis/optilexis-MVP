import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:optilexis_mobile/main.dart';
import 'package:optilexis_mobile/src/api_client.dart';

class FakeApi extends OptilexisApi {
  @override
  Future<Map<String, dynamic>> health() async => {
        'status': 'ok', 'environment': 'development_simulation',
      };
  @override
  void dispose() {}
}

void main() {
  testWidgets('renders the branded development prototype', (tester) async {
    await tester.pumpWidget(OptilexisApp(api: FakeApi()));
    expect(find.text('OPTILEXIS'), findsOneWidget);
    expect(find.text('Plan a journey'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.textContaining('DEVELOPMENT SIMULATOR'), findsOneWidget);
  });
}
