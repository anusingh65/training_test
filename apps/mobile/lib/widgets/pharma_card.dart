import 'package:flutter/material.dart';
import '../config/theme.dart';

class PharmaCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets padding;

  const PharmaCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: child,
    );
  }
}
