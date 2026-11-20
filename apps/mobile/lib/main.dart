import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'src/api_client.dart';
import 'src/design.dart';
import 'src/models.dart';

void main() => runApp(const OptilexisApp());

class OptilexisApp extends StatelessWidget {
  const OptilexisApp({super.key, this.api});

  final OptilexisApi? api;

  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'Optilexis',
        theme: optilexisTheme(),
        home: JourneyHome(api: api),
      );
}

const _languages = <String, String>{
  'en': 'English',
  'ja': 'Japanese',
  'fr': 'French',
  'es': 'Spanish',
  'de': 'German',
  'zh': 'Chinese',
  'th': 'Thai',
};
const _eventLabels = <String, String>{
  'airport_approach': 'Approaching an airport',
  'station_approach': 'Entering a railway station',
  'hotel_approach': 'Approaching a hotel',
  'parking_approach': 'Arriving at a parking area',
  'off_route': 'Route needs review',
};
const _phraseLabels = <String, String>{
  'hotel_checkin': 'Hotel check-in',
  'station_platform': 'Platform directions',
  'airport_terminal': 'Airport terminal',
  'parking_question': 'Parking permission',
};

class JourneyHome extends StatefulWidget {
  const JourneyHome({super.key, this.api});

  final OptilexisApi? api;
  @override
  State<JourneyHome> createState() => _JourneyHomeState();
}

class _JourneyHomeState extends State<JourneyHome> {
  final _destination = TextEditingController(text: 'Shinjuku Station, Tokyo');
  final _debugToken = TextEditingController();
  late final OptilexisApi _api;
  late final bool _ownsApi;

  String _language = 'ja';
  String _mode = 'walk';
  String _navigation = 'maps_handoff';
  bool _consentLocation = false;
  bool _consentMicrophone = false;
  bool _parked = false;
  bool _busy = false;
  bool _backendOnline = false;
  String? _error;
  JourneyDto? _journey;
  EventOutcomeDto? _lastOutcome;
  PhraseDto? _lastPhrase;
  List<JourneyDto> _history = [];
  bool _authenticated = false;

  @override
  void initState() {
    super.initState();
    _ownsApi = widget.api == null;
    _api = widget.api ?? OptilexisApi();
    final configured = _api.debugTokenConfigured;
    _pingBackend();
    if (configured) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _loadHistory();
      });
    }
  }

  @override
  void dispose() {
    _destination.dispose();
    _debugToken.dispose();
    if (_ownsApi) _api.dispose();
    super.dispose();
  }

  Future<void> _pingBackend() async {
    try {
      await _api.health();
      if (mounted) setState(() => _backendOnline = true);
    } catch (_) {
      if (mounted) setState(() => _backendOnline = false);
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await action();
      if (mounted) setState(() => _backendOnline = true);
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = '$error';
          _backendOnline = false;
        });
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _loadHistory() => _run(() async {
        final history = await _api.listJourneys();
        if (!mounted) return;
        setState(() {
          _history = history;
          _authenticated = true;
          if (_journey == null) {
            for (final trip in history) {
              if (trip.active) {
                _journey = trip;
                _language = trip.language;
                _mode = trip.mode;
                _navigation = trip.navigationMode;
                _consentLocation = trip.consent.location;
                _consentMicrophone = trip.consent.microphone;
                break;
              }
            }
          }
        });
      });

  Future<void> _signIn() async {
    _api.setDebugToken(_debugToken.text);
    await _loadHistory();
    _debugToken.clear();
  }

  Future<void> _start() => _run(() async {
        if (_destination.text.trim().length < 2) {
          throw const OptilexisApiException('Enter a destination first');
        }
        final created = await _api.createJourney(
          destination: _destination.text.trim(),
          language: _language,
          mode: _mode,
          navigationMode: _navigation,
          consentLocation: _consentLocation,
          consentMicrophone: _consentMicrophone,
        );
        setState(() {
          _journey = created;
          _history = [created, ..._history];
          _lastOutcome = null;
          _lastPhrase = null;
          _parked = false;
        });
      });

  Future<void> _event(String event) => _run(() async {
        final outcome = await _api.sendSimulationEvent(
          journeyId: _journey!.id,
          event: event,
          parked: _parked,
        );
        setState(() => _lastOutcome = outcome);
      });

  Future<void> _phrase(String key) => _run(() async {
        final phrase = await _api.demoPhrase(
          phraseKey: key,
          language: _language,
        );
        setState(() => _lastPhrase = phrase);
      });

  Future<void> _end() => _run(() async {
        final closed = await _api.closeJourney(_journey!.id);
        setState(() {
          _history = _history.map((item) => item.id == closed.id ? closed : item).toList();
          _journey = null;
          _lastOutcome = null;
          _lastPhrase = null;
        });
      });

  Future<void> _handoff() async {
    final destination = _journey?.destination;
    if (destination == null) return;
    final uri = Uri.https('www.google.com', '/maps/dir/', {
      'api': '1',
      'destination': destination,
      'travelmode': _mode == 'walk' ? 'walking' : 'driving',
    });
    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!opened && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open external navigation')),
      );
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('OPTILEXIS', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 2)),
              Text('One journey. Every language.',
                  style: TextStyle(fontSize: 11, color: optilexisMuted)),
            ],
          ),
          actions: [
            if (_authenticated && kDebugMode) IconButton(
              tooltip: 'Sign out of development account',
              onPressed: _busy ? null : () {
                _api.clearDebugToken();
                setState(() {
                  _authenticated = false;
                  _journey = null;
                  _history = [];
                  _lastOutcome = null;
                  _lastPhrase = null;
                });
              },
              icon: const Icon(Icons.logout_outlined),
            ),
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Icon(
                _backendOnline ? Icons.cloud_done_outlined : Icons.cloud_off_outlined,
                color: _backendOnline ? optilexisTeal : Colors.orangeAccent,
              ),
            ),
          ],
        ),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 740),
              child: ListView(
                padding: const EdgeInsets.all(18),
                children: [
                  _prototypeBanner(),
                  if (kDebugMode && !_authenticated) _developmentSignInCard(),
                  if (!kDebugMode && !_authenticated) _notice('OIDC sign-in integration is pending provider registration. Release mode has no development token fallback.', Colors.orangeAccent),
                  if (_error != null) _notice(_error!, Colors.orangeAccent),
                  if (_authenticated) ...[
                    if (_journey == null) _setupCard() else _activeJourneyCard(),
                    _historyCard(),
                  ],
                  if (_authenticated && _journey != null) ...[
                    const SizedBox(height: 10),
                    _simulationCard(),
                    if (_lastOutcome != null) _outcomeCard(),
                    _phraseCard(),
                    if (_lastPhrase != null) _phraseResultCard(),
                    _endJourneyCard(),
                  ],
                  _devicesCard(),
                  const SizedBox(height: 16),
                  const Text(
                    'Pilot foundation • No live GPS, ASR, TTS, HERE navigation, Meta or Vantrue connection.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: optilexisMuted, fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ),
      );

  Widget _developmentSignInCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _section('Development sign in'),
            const Text('Enter the local pilot token configured on your development server. Tokens are held in memory only; production OIDC login is not yet enabled.'),
            const SizedBox(height: 12),
            TextField(
              controller: _debugToken,
              obscureText: true,
              autocorrect: false,
              enableSuggestions: false,
              decoration: const InputDecoration(labelText: 'Development bearer token'),
            ),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _busy ? null : _signIn, child: const Text('Verify development identity')),
          ]),
        ),
      );

  Widget _historyCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _section('My journeys (persisted)'),
            OutlinedButton(onPressed: _busy ? null : _loadHistory, child: const Text('Refresh my journeys')),
            if (_history.isEmpty) const Text('No journeys saved for this identity'),
            ..._history.take(8).map((trip) => ListTile(
              title: Text(trip.destination),
              subtitle: Text(trip.active ? 'Active • ${trip.stage}' : 'Closed • ${trip.stage}'),
              trailing: trip.active ? const Icon(Icons.play_circle_outline) : const Icon(Icons.check_circle_outline),
              onTap: trip.active && !_busy ? () => setState(() {
                _journey = trip;
                _language = trip.language;
                _mode = trip.mode;
                _navigation = trip.navigationMode;
                _lastOutcome = null;
                _lastPhrase = null;
              }) : null,
            )),
          ]),
        ),
      );

  Widget _prototypeBanner() => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: optilexisDeep,
          border: Border.all(color: optilexisTeal.withValues(alpha: .35)),
          borderRadius: BorderRadius.circular(16),
        ),
        child: const Row(children: [
          Icon(Icons.science_outlined, color: optilexisTeal),
          SizedBox(width: 10),
          Expanded(
            child: Text('DEVELOPMENT SIMULATOR • Context events are manually triggered. No real route tracking.'),
          ),
        ]),
      );

  Widget _notice(String message, Color color) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(message, style: TextStyle(color: color)),
        ),
      );

  Widget _section(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 13),
        child: Text(text, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
      );

  Widget _setupCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _section('Plan a journey'),
            TextField(
              controller: _destination,
              maxLength: 160,
              decoration: const InputDecoration(labelText: 'Destination', prefixIcon: Icon(Icons.place_outlined)),
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              value: _language,
              decoration: const InputDecoration(labelText: 'Language for assistance'),
              items: _languages.entries
                  .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                  .toList(),
              onChanged: _busy ? null : (value) => setState(() => _language = value ?? _language),
            ),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'walk', label: Text('Walking'), icon: Icon(Icons.directions_walk)),
                ButtonSegment(value: 'drive', label: Text('Driving'), icon: Icon(Icons.directions_car_outlined)),
              ],
              selected: {_mode},
              onSelectionChanged: (value) => setState(() => _mode = value.first),
            ),
            const SizedBox(height: 14),
            DropdownButtonFormField<String>(
              value: _navigation,
              decoration: const InputDecoration(labelText: 'Navigation mode'),
              items: const [
                DropdownMenuItem(value: 'maps_handoff', child: Text('External Maps handoff')),
                DropdownMenuItem(value: 'own_route', child: Text('Optilexis route (SDK pending)')),
              ],
              onChanged: (value) => setState(() => _navigation = value ?? _navigation),
            ),
            SwitchListTile(
              value: _consentLocation,
              title: const Text('Allow location when implemented'),
              subtitle: const Text('This starter does not access phone location.'),
              onChanged: (value) => setState(() => _consentLocation = value),
            ),
            SwitchListTile(
              value: _consentMicrophone,
              title: const Text('Allow microphone when implemented'),
              subtitle: const Text('No microphone recording is active in this build.'),
              onChanged: (value) => setState(() => _consentMicrophone = value),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: _busy ? null : _start,
              icon: const Icon(Icons.route_outlined),
              label: Text(_busy ? 'Starting…' : 'Start development journey'),
            ),
          ]),
        ),
      );

  Widget _activeJourneyCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _section('Journey active'),
            Text(_journey!.destination,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            const SizedBox(height: 7),
            Text('Mode: $_mode • Language: ${_languages[_language]}',
                style: const TextStyle(color: optilexisMuted)),
            const SizedBox(height: 12),
            if (_navigation == 'maps_handoff')
              OutlinedButton.icon(
                onPressed: _handoff,
                icon: const Icon(Icons.open_in_new),
                label: const Text('Open directions in Google Maps'),
              )
            else
              const Text('Own-route navigation will require a licensed HERE SDK integration. No guidance is active.'),
            const Text('External Maps do not share live turn events with Optilexis.',
                style: TextStyle(color: optilexisMuted, fontSize: 12)),
          ]),
        ),
      );

  Widget _simulationCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _section('Try a context event'),
            const Text('Simulated only — tap a journey event to test prediction and safety policy.'),
            if (_mode == 'drive') SwitchListTile(
              title: const Text('Vehicle parked'),
              subtitle: const Text('Turn off to test moving-vehicle suppression'),
              value: _parked,
              onChanged: (value) => setState(() => _parked = value),
            ),
            const SizedBox(height: 8),
            ..._eventLabels.entries.map((e) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: OutlinedButton(
                    onPressed: _busy ? null : () => _event(e.key),
                    child: Text(e.value),
                  ),
                )),
          ]),
        ),
      );

  Widget _outcomeCard() {
    final suggestion = _lastOutcome!.suggestion;
    final suppressed = _lastOutcome!.suppressed;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          _section(suppressed ? 'Prompt suppressed' : 'Predictive recommendation'),
          if (suppressed)
            Text('${_lastOutcome!.reason}', style: const TextStyle(color: Colors.orangeAccent))
          else if (suggestion != null) ...[
            Text(suggestion.title, style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text(suggestion.message),
            const SizedBox(height: 8),
            Text('Next action: ${suggestion.action}',
                style: const TextStyle(color: optilexisTeal)),
          ],
          const SizedBox(height: 10),
          const Text('Simulation output • Not a navigation, traffic or legal instruction.',
              style: TextStyle(fontSize: 12, color: optilexisMuted)),
        ]),
      ),
    );
  }

  Widget _phraseCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            _section('Curated phrasebook'),
            const Text('Test prepared multilingual phrases. Live speech translation is not connected.'),
            const SizedBox(height: 8),
            ..._phraseLabels.entries.map((e) => OutlinedButton(
                  onPressed: _busy ? null : () => _phrase(e.key),
                  child: Text(e.value),
                )),
          ]),
        ),
      );

  Widget _phraseResultCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _section('Translated demo phrase'),
            Text(_lastPhrase!.sourceText, style: const TextStyle(color: optilexisMuted)),
            const SizedBox(height: 12),
            SelectableText(_lastPhrase!.translatedText,
                style: const TextStyle(fontSize: 20, color: optilexisTeal)),
            const SizedBox(height: 8),
            const Text('Curated demonstration, not real-time translation or audio.',
                style: TextStyle(color: optilexisMuted, fontSize: 12)),
          ]),
        ),
      );

  Widget _endJourneyCard() => Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: TextButton.icon(
          onPressed: _busy ? null : _end,
          icon: const Icon(Icons.stop_circle_outlined),
          label: const Text('End journey'),
        ),
      );

  Widget _devicesCard() => Card(
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _section('Device integrations'),
            _deviceRow(Icons.spatial_audio_off, 'Meta glasses', 'Native toolkit bridge pending'),
            _deviceRow(Icons.videocam_off_outlined, 'Vantrue E1 Pro S', 'Live video API unverified'),
            _deviceRow(Icons.directions_car_outlined, 'CarPlay / Android Auto', 'Platform eligibility pending'),
            _deviceRow(Icons.map_outlined, 'HERE Navigate', 'Licensed SDK integration pending'),
          ]),
        ),
      );

  Widget _deviceRow(IconData icon, String name, String status) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 9),
        child: Row(children: [
          Icon(icon, color: optilexisTeal),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(name, style: const TextStyle(fontWeight: FontWeight.w600)),
            Text(status, style: const TextStyle(fontSize: 12, color: optilexisMuted)),
          ])),
        ]),
      );
}
