import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'screens/splash/splash_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/consumer/home_screen.dart';
import 'screens/consumer/scan_screen.dart';
import 'screens/consumer/result_screen.dart';
import 'screens/consumer/drug_details_screen.dart';
import 'screens/consumer/report_screen.dart';
import 'screens/consumer/history_screen.dart';
import 'screens/commuter/commuter_home_screen.dart';
import 'screens/commuter/scan_receive_screen.dart';
import 'screens/commuter/confirm_transfer_screen.dart';
import 'screens/shared/profile_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(path: '/', builder: (_, __) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/home', builder: (_, __) => const ConsumerHomeScreen()),
      GoRoute(path: '/scan', builder: (_, __) => const ScanScreen()),
      GoRoute(
        path: '/result',
        builder: (_, state) => ResultScreen(
          data: state.extra as Map<String, dynamic>? ?? {},
        ),
      ),
      GoRoute(
        path: '/drug/:drugId',
        builder: (_, state) => DrugDetailsScreen(
          drugId: state.pathParameters['drugId']!,
        ),
      ),
      GoRoute(
        path: '/report/:drugId',
        builder: (_, state) => ReportScreen(
          drugId: state.pathParameters['drugId']!,
        ),
      ),
      GoRoute(path: '/history', builder: (_, __) => const HistoryScreen()),
      GoRoute(path: '/commuter', builder: (_, __) => const CommuterHomeScreen()),
      GoRoute(path: '/commuter/scan', builder: (_, __) => const ScanReceiveScreen()),
      GoRoute(
        path: '/commuter/confirm',
        builder: (_, state) => ConfirmTransferScreen(
          data: state.extra as Map<String, dynamic>? ?? {},
        ),
      ),
      GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
    ],
  );
});
