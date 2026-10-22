// lib/widgets/trust_badge.dart

import 'package:flutter/material.dart';

class TrustBadge extends StatelessWidget {
  final int score;
  final String status;

  const TrustBadge({super.key, required this.score, required this.status});

  Color get color {
    if (score >= 80) return Colors.green;
    if (score >= 50) return Colors.orange;
    if (score >= 20) return Colors.red;
    return Colors.red.shade900;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 140,
          height: 140,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: color.withOpacity(0.15),
            border: Border.all(color: color, width: 8),
          ),
          child: Center(
            child: Text(
              score.toString(),
              style: TextStyle(
                fontSize: 48,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          status,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }
}