# MediChain Manufacturer App

A Flutter-based mobile application for pharmaceutical manufacturers to register medicine batches on the blockchain and generate QR codes for supply chain tracking.

## Features

✅ **WalletConnect Integration** - Secure authentication with mobile wallets (MetaMask, Trust Wallet, etc.)
✅ **Batch Management** - Create and manage medicine batches
✅ **IPFS Storage** - Store medicine metadata on Pinata IPFS
✅ **QR Code Generation** - Generate QR codes for individual strips and batches
✅ **Blockchain Integration** - Register medicines on Ethereum Sepolia testnet
✅ **PDF Export** - Generate printable PDF sheets with QR codes

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Flutter Mobile App                    │
├─────────────────────────────────────────────────┤
│                                                 │
│   WalletConnect ──► Ethereum Wallet             │
│        │                                        │
│        ▼                                        │
│   Smart Contracts (Sepolia)                    │
│   - PharmaChainCore                            │
│   - PharmaChainBatch                           │
│        │                                        │
│        ▼                                        │
│   Pinata IPFS ──► Metadata Storage             │
│        │                                        │
│        ▼                                        │
│   QR Code Generation ──► Print/Export          │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Prerequisites

- Flutter SDK (3.9.2 or later)
- Android Studio / Xcode
- Pinata Account (https://pinata.cloud)
- WalletConnect Project ID (https://cloud.walletconnect.com)
- Mobile wallet app (MetaMask, Trust Wallet, etc.)

### 2. Install Dependencies

```bash
flutter pub get
```

### 3. Configure API Keys

Edit `lib/config/app_config.dart` and add your credentials:

```dart
// Pinata IPFS
static const String pinataApiKey = 'YOUR_PINATA_API_KEY';
static const String pinataSecretKey = 'YOUR_PINATA_SECRET_KEY';
static const String pinataJwt = 'YOUR_PINATA_JWT_TOKEN';

// WalletConnect
static const String wcProjectId = 'YOUR_WALLETCONNECT_PROJECT_ID';
```

**SECURITY WARNING:** In production, use environment variables or Flutter's --dart-define for sensitive keys.

### 4. Register as Manufacturer

Before using the app, your wallet address must be registered as a Manufacturer on the blockchain.

Contact the admin or use the admin portal to register:

```solidity
// Example: Using Hardhat console
const core = await ethers.getContractAt("PharmaChainCore", CORE_ADDRESS);
await core.registerActor(
    "0xYourWalletAddress",
    1,  // Role.Manufacturer
    "Your Company Name",
    "Your Location"
);
```

### 5. Run the App

```bash
# Android
flutter run

# iOS
flutter run -d ios
```

## Usage Flow

### 1. Login
- Open the app
- Tap "Connect Wallet"
- Scan QR code with your mobile wallet (MetaMask, Trust Wallet, etc.)
- Approve the connection
- App verifies you have Manufacturer role

### 2. Create Batch
- Tap "New Batch" button on dashboard
- Fill in batch details:
  - Batch Number (e.g., "BATCH-2024-001")
  - Total Units (number of medicine strips)
  - Medicine Name (e.g., "Paracetamol 500mg")
  - Composition
  - Dosage
  - Manufacture Date
  - Expiry Date
  - Manufacturer Details
- Submit to create batch on blockchain

### 3. Register Strips
- Open the created batch
- Tap "Register Strips"
- App will:
  - Generate auto-incremented medicine IDs (e.g., 1001001, 1001002...)
  - Upload each strip metadata to Pinata IPFS
  - Calculate SHA-256 content hash
  - Generate QR code for each strip
  - Bulk register on blockchain (in chunks of 100)

### 4. Generate Batch QR
- After all strips are registered
- Tap "Generate Batch QR"
- App creates batch QR containing all medicine IDs
- This QR goes on the carton

### 5. Export QR Codes
- Tap "Export QR Codes"
- Choose format:
  - **Print** - Send to printer
  - **Share PDF** - Share via email/messaging
  - **Save PDF** - Save to device

PDF contains:
- Batch QR (for carton)
- Individual strip QRs (for aluminum foil)
- Batch details
- 4 QR codes per page in 2x2 grid

## Project Structure

```
lib/
├── config/
│   ├── app_config.dart          # API keys, contract addresses
│   └── contract_config.dart     # Smart contract ABIs
├── models/
│   ├── batch_model.dart         # Batch data model
│   ├── medicine_model.dart      # Medicine data model
│   └── manufacturer_model.dart   # Manufacturer data model
├── services/
│   ├── blockchain_service.dart  # Ethereum contract interactions
│   ├── pinata_service.dart      # IPFS storage
│   ├── wallet_service.dart      # WalletConnect integration
│   └── qr_service.dart          # QR code generation & PDF export
├── screens/
│   ├── auth/
│   │   └── login_screen.dart    # WalletConnect login
│   ├── dashboard/
│   │   └── dashboard_screen.dart # Batch list
│   ├── batch/
│   │   ├── create_batch_screen.dart    # Create new batch
│   │   ├── batch_detail_screen.dart    # Batch details & actions
│   │   └── register_strips_screen.dart  # Strip registration
│   └── qr/
│       └── qr_viewer_screen.dart # QR code viewer & export
└── main.dart                    # App entry point
```

## Smart Contract Integration

### Contracts (Sepolia Testnet)

```
PharmaChainCore:   0x42b07481379ce4beF2aC70BC0329bD29a2E7cb8A
PharmaChainBatch:  0x555d8aFe7FD29eC64D84e930b1Bf0265D1cC68A
PharmaChainScanner: 0x710a91E26754c126C3A1b8C0E0c5b06568d85493
```

### Key Functions Used

**PharmaChainBatch**
- `createBatch()` - Create new batch on blockchain
- `addMedicinesToBatch()` - Bulk register medicines (max 100 per tx)
- `completeBatch()` - Mark batch as complete
- `getBatch()` - Get batch details
- `getManufacturerBatches()` - Get all batches for manufacturer

**PharmaChainCore**
- `getActorRole()` - Check user role
- `isMedicineRegistered()` - Check if medicine ID exists

## Workflow Details

### Medicine ID Generation

Medicine IDs are auto-generated using the pattern:
```
Medicine ID = Batch ID + Sequential Number

Example:
Batch ID: 1001
Medicine IDs: 1001001, 1001002, 1001003, ...
```

This ensures:
- Unique IDs across the system
- Traceability back to batch
- Simple incrementing logic

### IPFS Metadata Structure

**Batch Metadata:**
```json
{
  "batch_id": 1001,
  "batch_number": "BATCH-2024-001",
  "total_units": 1000,
  "medicine_name": "Paracetamol 500mg",
  "composition": "Paracetamol 500mg, Excipients q.s.",
  "dosage": "1-2 tablets every 4-6 hours",
  "manufacture_date": "2024-01-15T00:00:00.000Z",
  "expiry_date": "2026-01-15T00:00:00.000Z",
  "manufacturer": {
    "name": "Cipla Ltd",
    "license": "MFG-MH-001234",
    "location": "Mumbai, Maharashtra",
    "address": "0x..."
  },
  "schema_version": "1.0",
  "type": "batch_metadata"
}
```

**Medicine Metadata:**
```json
{
  "medicine_id": 1001001,
  "batch_id": 1001,
  "batch_number": "BATCH-2024-001",
  "name": "Paracetamol 500mg",
  "composition": "Paracetamol 500mg, Excipients q.s.",
  "dosage": "1-2 tablets every 4-6 hours",
  "manufacture_date": "2024-01-15T00:00:00.000Z",
  "expiry_date": "2026-01-15T00:00:00.000Z",
  "schema_version": "1.0",
  "type": "medicine_metadata"
}
```

### Blockchain Verification

Each medicine has:
1. **Medicine ID** - Unique identifier (encoded in QR)
2. **IPFS Hash** - Points to metadata on IPFS
3. **Content Hash** - SHA-256 hash of metadata for integrity verification

Consumers can verify authenticity by:
1. Scanning QR code to get Medicine ID
2. Querying blockchain for IPFS hash
3. Fetching metadata from IPFS
4. Calculating SHA-256 and comparing with blockchain

## Troubleshooting

### "Wallet not connected"
- Ensure your wallet app is open
- Check that you're on Sepolia network
- Try disconnecting and reconnecting

### "Access denied: Not a manufacturer"
- Your address must be registered on blockchain first
- Contact admin to register your address with Role = 1 (Manufacturer)

### "Pinata upload failed"
- Check your API keys in app_config.dart
- Verify you have Pinata credits
- Check internet connection

### "Transaction failed"
- Ensure you have Sepolia ETH for gas fees
- Check if medicine ID already exists
- Verify batch is not marked as complete

## Gas Optimization

The app uses bulk registration to save gas:
- Registers up to 100 medicines per transaction
- For 1000 medicine batch = ~10 transactions
- Estimated gas per transaction: ~0.001 ETH on Sepolia

## Security Considerations

1. **Private Keys** - Never stored in app, managed by WalletConnect
2. **API Keys** - Should be environment variables in production
3. **Content Hash** - Ensures IPFS data integrity
4. **Role Verification** - Enforced on-chain before any operations

## Future Enhancements

- [ ] Multi-language support
- [ ] Batch templates for common medicines
- [ ] QR scanner for verification
- [ ] Push notifications for batch events
- [ ] Analytics dashboard
- [ ] Export to CSV/Excel
- [ ] Barcode integration
- [ ] Offline mode with sync

## Support

For issues or questions:
- GitHub: https://github.com/Madglog/MediChain/issues
- Smart Contracts: See `context/PharmaChain/README.md`
- API Integration: See `context/PharmaChain/MOBILE_APP_INTEGRATION_GUIDE.md`

## License

MIT License - See LICENSE file for details
