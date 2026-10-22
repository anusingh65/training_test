import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../models/custody_event.dart';

class TimelineWidget extends StatelessWidget {
  final List<CustodyEvent> events;

  const TimelineWidget({super.key, required this.events});

  IconData _eventIcon(String type) {
    switch (type) {
      case 'manufactured':
        return Icons.factory;
      case 'shipped':
        return Icons.local_shipping;
      case 'received':
        return Icons.warehouse;
      case 'delivered':
        return Icons.store;
      default:
        return Icons.circle;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: events.asMap().entries.map((entry) {
        final i = entry.key;
        final event = entry.value;
        final isLast = i == events.length - 1;

        return IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Timeline line + dot
              SizedBox(
                width: 40,
                child: Column(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.primary),
                      ),
                      child: Icon(_eventIcon(event.eventType),
                          size: 16, color: AppColors.primary),
                    ),
                    if (!isLast)
                      Expanded(
                        child: Container(
                          width: 2,
                          color: AppColors.border,
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              // Content
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        event.eventType.toUpperCase(),
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                          color: AppColors.primary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      if (event.toEntity != null)
                        Text(event.toEntity!, style: const TextStyle(fontSize: 13)),
                      if (event.location != null)
                        Text(event.location!,
                            style: const TextStyle(fontSize: 12, color: Colors.grey)),
                      Text(
                        event.timestamp.toLocal().toString().substring(0, 16),
                        style: const TextStyle(fontSize: 11, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}
