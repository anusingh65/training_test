-- PharmaChain Seed Data
-- Note: Run after migrations. UUIDs for profiles assume Supabase auth users exist.
-- For demo, we insert directly with generated UUIDs.

-- Sample drugs (25 entries)
INSERT INTO drugs (drug_id, batch_id, name, manufacturer, manufacture_date, expiry_date, metadata_hash, qr_hash, ipfs_cid, status, flagged) VALUES
('DRG-001', 'BAT-2024-001', 'Amoxicillin 500mg', 'Sun Pharmaceuticals', '2024-06-15', '2026-06-15', 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2', 'qr_hash_001', 'QmXk8D1vZ2N3p4Q5r6S7t8U9v0W1x2Y3z4A5b6C7d8E9f0', 'verified', false),
('DRG-002', 'BAT-2024-001', 'Amoxicillin 500mg', 'Sun Pharmaceuticals', '2024-06-15', '2026-06-15', 'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3', 'qr_hash_002', 'QmY1E2f3G4h5I6j7K8l9M0n1O2p3Q4r5S6t7U8v9W0x1Y2', 'verified', false),
('DRG-003', 'BAT-2024-002', 'Paracetamol 650mg', 'Cipla Ltd', '2024-07-01', '2026-07-01', 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4', 'qr_hash_003', 'QmZ2F3g4H5i6J7k8L9m0N1o2P3q4R5s6T7u8V9w0X1y2Z3', 'verified', false),
('DRG-004', 'BAT-2024-002', 'Paracetamol 650mg', 'Cipla Ltd', '2024-07-01', '2026-07-01', 'd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5', 'qr_hash_004', NULL, 'verified', false),
('DRG-005', 'BAT-2024-003', 'Metformin 500mg', 'Dr. Reddys Labs', '2024-05-20', '2026-05-20', 'e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6', 'qr_hash_005', 'QmA3G4h5I6j7K8l9M0n1O2p3Q4r5S6t7U8v9W0x1Y2z3A4', 'verified', false),
('DRG-006', 'BAT-2024-004', 'Atorvastatin 10mg', 'Lupin Pharmaceuticals', '2024-08-10', '2026-08-10', 'f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1', 'qr_hash_006', 'QmB4H5i6J7k8L9m0N1o2P3q4R5s6T7u8V9w0X1y2Z3a4B5', 'verified', false),
('DRG-007', 'BAT-2024-005', 'Cetirizine 10mg', 'Mankind Pharma', '2024-09-01', '2026-09-01', 'a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3', 'qr_hash_007', NULL, 'verified', false),
('DRG-008', 'BAT-2024-006', 'Azithromycin 250mg', 'Zydus Lifesciences', '2024-04-15', '2025-10-15', 'b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4', 'qr_hash_008', 'QmC5I6j7K8l9M0n1O2p3Q4r5S6t7U8v9W0x1Y2z3A4b5C6', 'suspicious', false),
('DRG-009', 'BAT-2024-007', 'Omeprazole 20mg', 'Torrent Pharmaceuticals', '2024-03-10', '2025-09-10', 'c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5', 'qr_hash_009', NULL, 'suspicious', false),
('DRG-010', 'BAT-2024-008', 'Ibuprofen 400mg', 'Alkem Laboratories', '2024-02-28', '2025-08-28', 'd5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6', 'qr_hash_010', 'QmD6J7k8L9m0N1o2P3q4R5s6T7u8V9w0X1y2Z3a4B5c6D7', 'counterfeit', true),
('DRG-011', 'BAT-2024-009', 'Losartan 50mg', 'Aurobindo Pharma', '2024-07-20', '2026-07-20', 'e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7', 'qr_hash_011', 'QmE7K8l9M0n1O2p3Q4r5S6t7U8v9W0x1Y2z3A4b5C6d7E8', 'verified', false),
('DRG-012', 'BAT-2024-010', 'Ciprofloxacin 500mg', 'Glenmark Pharma', '2024-06-05', '2026-06-05', 'f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2b3c4d5e6f7a2', 'qr_hash_012', NULL, 'verified', false),
('DRG-013', 'BAT-2024-011', 'Pantoprazole 40mg', 'Cadila Healthcare', '2024-08-25', '2026-08-25', 'a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4', 'qr_hash_013', 'QmF8L9m0N1o2P3q4R5s6T7u8V9w0X1y2Z3a4B5c6D7e8F9', 'verified', false),
('DRG-014', 'BAT-2024-012', 'Clopidogrel 75mg', 'Sun Pharmaceuticals', '2024-01-15', '2025-07-15', 'b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5', 'qr_hash_014', NULL, 'suspicious', false),
('DRG-015', 'BAT-2024-013', 'Montelukast 10mg', 'Cipla Ltd', '2024-09-10', '2026-09-10', 'c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6', 'qr_hash_015', 'QmG9M0n1O2p3Q4r5S6t7U8v9W0x1Y2z3A4b5C6d7E8f9G0', 'verified', false),
('DRG-016', 'BAT-2024-014', 'Doxycycline 100mg', 'Mankind Pharma', '2024-05-05', '2025-11-05', 'd6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7', 'qr_hash_016', NULL, 'counterfeit', true),
('DRG-017', 'BAT-2024-015', 'Amlodipine 5mg', 'Dr. Reddys Labs', '2024-10-01', '2026-10-01', 'e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8', 'qr_hash_017', 'QmH0N1o2P3q4R5s6T7u8V9w0X1y2Z3a4B5c6D7e8F9g0H1', 'verified', false),
('DRG-018', 'BAT-2024-016', 'Levofloxacin 750mg', 'Torrent Pharmaceuticals', '2024-04-20', '2025-10-20', 'f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3b4c5d6e7f8a3', 'qr_hash_018', NULL, 'suspicious', false),
('DRG-019', 'BAT-2024-017', 'Gabapentin 300mg', 'Lupin Pharmaceuticals', '2024-11-15', '2026-11-15', 'a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5', 'qr_hash_019', 'QmI1O2p3Q4r5S6t7U8v9W0x1Y2z3A4b5C6d7E8f9G0h1I2', 'verified', false),
('DRG-020', 'BAT-2024-018', 'Diclofenac 50mg', 'Alkem Laboratories', '2024-03-01', '2025-09-01', 'b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6', 'qr_hash_020', NULL, 'verified', false),
('DRG-021', 'BAT-2024-019', 'Hydroxychloroquine 200mg', 'Zydus Lifesciences', '2024-07-10', '2026-07-10', 'c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7', 'qr_hash_021', 'QmJ2P3q4R5s6T7u8V9w0X1y2Z3a4B5c6D7e8F9g0H1i2J3', 'verified', false),
('DRG-022', 'BAT-2024-020', 'Telmisartan 40mg', 'Glenmark Pharma', '2024-08-05', '2026-08-05', 'd7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8', 'qr_hash_022', NULL, 'verified', false),
('DRG-023', 'BAT-2024-021', 'Ranitidine 150mg', 'Cadila Healthcare', '2024-01-20', '2025-01-20', 'e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9', 'qr_hash_023', 'QmK3Q4r5S6t7U8v9W0x1Y2z3A4b5C6d7E8f9G0h1I2j3K4', 'counterfeit', true),
('DRG-024', 'BAT-2024-022', 'Metoprolol 50mg', 'Aurobindo Pharma', '2024-10-15', '2026-10-15', 'f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4b5c6d7e8f9a4', 'qr_hash_024', NULL, 'verified', false),
('DRG-025', 'BAT-2024-023', 'Vitamin D3 60000IU', 'Sun Pharmaceuticals', '2024-11-01', '2026-11-01', 'a5b6c7d8e9f0a5b6c7d8e9f0a5b6c7d8e9f0a5b6c7d8e9f0a5b6c7d8e9f0a5b6', 'qr_hash_025', 'QmL4R5s6T7u8V9w0X1y2Z3a4B5c6D7e8F9g0H1i2J3k4L5', 'verified', false);

-- Custody events for demo supply chains
INSERT INTO custody_events (drug_id, from_entity, to_entity, event_type, location, latitude, longitude, timestamp) VALUES
-- DRG-001 full chain
('DRG-001', NULL, 'Sun Pharmaceuticals', 'manufactured', 'Mumbai, Maharashtra', 19.0760, 72.8777, '2024-06-15 10:00:00+05:30'),
('DRG-001', 'Sun Pharmaceuticals', 'MedLogistics India', 'shipped', 'Mumbai, Maharashtra', 19.0760, 72.8777, '2024-06-16 08:00:00+05:30'),
('DRG-001', 'MedLogistics India', 'Delhi Distribution Hub', 'received', 'New Delhi', 28.6139, 77.2090, '2024-06-18 14:00:00+05:30'),
('DRG-001', 'Delhi Distribution Hub', 'Apollo Pharmacy Connaught Place', 'delivered', 'New Delhi', 28.6315, 77.2167, '2024-06-19 11:00:00+05:30'),
-- DRG-003 chain
('DRG-003', NULL, 'Cipla Ltd', 'manufactured', 'Bengaluru, Karnataka', 12.9716, 77.5946, '2024-07-01 09:00:00+05:30'),
('DRG-003', 'Cipla Ltd', 'BlueDart Pharma', 'shipped', 'Bengaluru, Karnataka', 12.9716, 77.5946, '2024-07-02 07:00:00+05:30'),
('DRG-003', 'BlueDart Pharma', 'Chennai Warehouse', 'received', 'Chennai, Tamil Nadu', 13.0827, 80.2707, '2024-07-03 16:00:00+05:30'),
('DRG-003', 'Chennai Warehouse', 'MedPlus T. Nagar', 'delivered', 'Chennai, Tamil Nadu', 13.0418, 80.2341, '2024-07-04 10:00:00+05:30'),
-- DRG-010 suspicious chain (counterfeit)
('DRG-010', NULL, 'Alkem Laboratories', 'manufactured', 'Sikkim', 27.3389, 88.6065, '2024-02-28 10:00:00+05:30'),
('DRG-010', 'Alkem Laboratories', 'Unknown Distributor', 'shipped', 'Kolkata, West Bengal', 22.5726, 88.3639, '2024-03-02 09:00:00+05:30'),
('DRG-010', 'Unknown Distributor', 'Unlicensed Shop', 'delivered', 'Patna, Bihar', 25.6093, 85.1376, '2024-03-05 15:00:00+05:30'),
-- DRG-005 chain
('DRG-005', NULL, 'Dr. Reddys Labs', 'manufactured', 'Hyderabad, Telangana', 17.3850, 78.4867, '2024-05-20 08:00:00+05:30'),
('DRG-005', 'Dr. Reddys Labs', 'PharmaTrans Logistics', 'shipped', 'Hyderabad, Telangana', 17.3850, 78.4867, '2024-05-21 06:00:00+05:30'),
('DRG-005', 'PharmaTrans Logistics', 'Pune Distribution Center', 'received', 'Pune, Maharashtra', 18.5204, 73.8567, '2024-05-23 12:00:00+05:30'),
('DRG-005', 'Pune Distribution Center', 'Netmeds Pharmacy Kothrud', 'delivered', 'Pune, Maharashtra', 18.5074, 73.8077, '2024-05-24 09:00:00+05:30'),
-- DRG-016 suspicious chain (counterfeit)
('DRG-016', NULL, 'Mankind Pharma', 'manufactured', 'Rajasthan', 26.9124, 75.7873, '2024-05-05 10:00:00+05:30'),
('DRG-016', 'Mankind Pharma', 'Suspicious Trader', 'shipped', 'Lucknow, UP', 26.8467, 80.9462, '2024-05-08 11:00:00+05:30');

-- Verification scans
INSERT INTO verification_scans (drug_id, scanner_role, location, latitude, longitude, result, risk_score, hash_matched, blockchain_verified, scanned_at) VALUES
('DRG-001', 'consumer', 'New Delhi', 28.6315, 77.2167, 'verified', 12.5, true, true, '2024-06-20 15:30:00+05:30'),
('DRG-001', 'consumer', 'New Delhi', 28.6280, 77.2190, 'verified', 10.0, true, true, '2024-06-21 10:00:00+05:30'),
('DRG-003', 'consumer', 'Chennai', 13.0418, 80.2341, 'verified', 8.3, true, true, '2024-07-05 14:00:00+05:30'),
('DRG-010', 'consumer', 'Patna', 25.6093, 85.1376, 'counterfeit', 92.1, false, false, '2024-03-10 16:00:00+05:30'),
('DRG-010', 'consumer', 'Gaya', 24.7955, 85.0002, 'counterfeit', 95.3, false, false, '2024-03-12 11:00:00+05:30'),
('DRG-005', 'consumer', 'Pune', 18.5074, 73.8077, 'verified', 15.2, true, true, '2024-05-25 09:00:00+05:30'),
('DRG-008', 'consumer', 'Ahmedabad', 23.0225, 72.5714, 'suspicious', 67.8, true, false, '2024-09-15 13:00:00+05:30'),
('DRG-016', 'consumer', 'Lucknow', 26.8467, 80.9462, 'counterfeit', 88.9, false, false, '2024-06-01 10:00:00+05:30'),
('DRG-009', 'consumer', 'Jaipur', 26.9124, 75.7873, 'suspicious', 55.4, true, true, '2024-08-20 12:00:00+05:30'),
('DRG-023', 'consumer', 'Kolkata', 22.5726, 88.3639, 'counterfeit', 91.7, false, false, '2024-05-15 14:00:00+05:30');

-- Flagged reports
INSERT INTO flagged_reports (drug_id, reason, description, severity, status, location, latitude, longitude, created_at) VALUES
('DRG-010', 'Hash mismatch', 'QR code hash does not match database records. Packaging appears tampered.', 'critical', 'confirmed', 'Patna, Bihar', 25.6093, 85.1376, '2024-03-10 16:05:00+05:30'),
('DRG-016', 'Suspicious packaging', 'Blister pack printing quality is poor, batch number font differs from authentic product.', 'high', 'investigating', 'Lucknow, UP', 26.8467, 80.9462, '2024-06-01 10:10:00+05:30'),
('DRG-023', 'Expired product sold', 'Drug past expiry date being sold at unauthorized outlet.', 'critical', 'confirmed', 'Kolkata, West Bengal', 22.5726, 88.3639, '2024-05-15 14:05:00+05:30'),
('DRG-008', 'Unusual scan pattern', 'Multiple scans from different cities within hours - possible duplicate batch.', 'medium', 'investigating', 'Ahmedabad, Gujarat', 23.0225, 72.5714, '2024-09-15 13:10:00+05:30'),
('DRG-009', 'Blockchain mismatch', 'On-chain custody events do not match physical delivery records.', 'high', 'pending', 'Jaipur, Rajasthan', 26.9124, 75.7873, '2024-08-20 12:15:00+05:30'),
('DRG-014', 'Geographic anomaly', 'Drug scanned in location inconsistent with supply chain route.', 'medium', 'pending', 'Surat, Gujarat', 21.1702, 72.8311, '2024-10-05 09:30:00+05:30');
