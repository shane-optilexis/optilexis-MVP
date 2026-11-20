import 'package:material_ui/material_ui.dart';

const optilexisNavy = Color(0xFF071629);
const optilexisDeep = Color(0xFF102B46);
const optilexisTeal = Color(0xFF11D3C2);
const optilexisMuted = Color(0xFF98B5C4);

ThemeData optilexisTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: optilexisTeal,
    brightness: Brightness.dark,
    surface: optilexisNavy,
  );
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: optilexisNavy,
    colorScheme: scheme,
    appBarTheme: const AppBarTheme(
      backgroundColor: optilexisNavy,
      foregroundColor: Colors.white,
      centerTitle: false,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: optilexisDeep,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
    ),
    cardTheme: CardThemeData(
      color: optilexisDeep,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      margin: const EdgeInsets.symmetric(vertical: 7),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: optilexisTeal,
        foregroundColor: optilexisNavy,
        minimumSize: const Size(0, 46),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    ),
  );
}
