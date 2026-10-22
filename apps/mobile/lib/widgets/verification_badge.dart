import 'package:flutter/material.dart';
import '../config/theme.dart';

class VerificationBadge extends StatelessWidget {
  final String status;

  const VerificationBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final Color color;
    final IconData icon;

    switch (status) {
      case 'verified':
        color = AppColors.verified;
        icon = Icons.check_circle;
        break;
      case 'suspicious':
        color = AppColors.suspicious;
        icon = Icons.warning;
        break;
      case 'counterfeit':
        color = AppColors.counterfeit;
        icon = Icons.dangerous;
        break;
      default:
        color = Colors.grey;
        icon = Icons.help_outline;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            status.toUpperCase(),
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color),
          ),
        ],
      ),
    );
  }
}
