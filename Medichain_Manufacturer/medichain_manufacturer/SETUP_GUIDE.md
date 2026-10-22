# MediChain Manufacturer App - Setup Guide

## Quick Start

### 1. Configure API Keys

Edit `lib/config/app_config.dart` and replace placeholder values:

```dart
// Pinata IPFS API Keys (Get from https://pinata.cloud)
static const String pinataApiKey = 'YOUR_PINATA_API_KEY';
static const String pinataSecretKey = 'YOUR_PINATA_SECRET_KEY';
static const String pinataJwt = 'YOUR_PINATA_JWT_TOKEN';

// WalletConnect Project ID (Get from https://cloud.walletconnect.com)
static const String wcProjectId = 'YOUR_WALLETCONNECT_PROJECT_ID';
```

### 2. Install Dependencies

```bash
flutter pub get
```

### 3. Run the App

```bash
flutter run
```

## Getting API Keys

### Pinata (IPFS Storage)

1. Go to https://pinata.cloud and sign up
2. Navigate to **API Keys** section
3. Create a new API key
4. Copy the **API Key**, **API Secret**, and **JWT**
5. Paste them in `lib/config/app_config.dart`

### WalletConnect

1. Go to https://cloud.walletconnect.com
2. Create a free account
3. Create a new project
4. Copy the **Project ID**
5. Paste it in `lib/config/app_config.dart`

## Register as Manufacturer

Before using the app, your wallet address must be registered on the blockchain as a Manufacturer.

### Option 1: Using Hardhat Console

```bash
cd context/PharmaChain
npx hardhat console --network sepolia
```

```javascript
const core = await ethers.getContractAt(
  "PharmaChainCore",
  "0x42b07481379ce4beF2aC70BC0329bD29a2E7cb8A"
);

await core.registerActor(
  "0xYourWalletAddress",  // Your wallet address
  1,                       // Role: Manufacturer
  "Your Company Name",
  "Your Location"
);
```

### Option 2: Using Admin Web Portal

Contact your system administrator to register your address through the admin portal.

## Testing the App

### 1. Connect Wallet
- Open the app
- Tap "Connect Wallet"
- Scan QR code with MetaMask or Trust Wallet
- Make sure you're on **Sepolia Testnet**

### 2. Get Test ETH
You need Sepolia ETH for gas fees:
- https://sepoliafaucet.com
- https://www.alchemy.com/faucets/ethereum-sepolia

### 3. Create Test Batch
- Tap "New Batch"
- Fill in test data:
  - Batch Number: TEST-001
  - Total Units: 10 (start small)
  - Medicine Name: Test Medicine
  - Fill other required fields
- Submit and wait for blockchain confirmation

### 4. Register Strips
- Open the created batch
- Tap "Register Strips"
- App will process all 10 strips
- This includes IPFS upload + blockchain registration

### 5. View Results
- Check dashboard for batch status
- All strips should be registered
- Ready for QR code generation

## Troubleshooting

### "Connection timeout"
- Check your internet connection
- RPC might be slow, try again
- Consider using your own Alchemy/Infura RPC URL

### "Transaction failed"
- Ensure you have enough Sepolia ETH
- Check if batch ID already exists
- Verify you're connected to the right network

### "IPFS upload failed"
- Verify Pinata API keys are correct
- Check Pinata account has remaining storage
- Try a smaller batch first

### "Access denied"
- Your address is not registered as manufacturer
- Follow the registration steps above
- Contact admin if issues persist

## Production Considerations

### Security

**DO NOT commit API keys to Git!**

For production, use environment variables:

```bash
flutter run --dart-define=PINATA_JWT=your_jwt_here \
            --dart-define=WC_PROJECT_ID=your_id_here
```

Then in code:

```dart
static const String pinataJwt = String.fromEnvironment('PINATA_JWT');
static const String wcProjectId = String.fromEnvironment('WC_PROJECT_ID');
```

### Performance

- For large batches (1000+ units), registration may take 5-10 minutes
- App processes in chunks of 100 to optimize gas
- Consider showing progress to users

### Network

- For production, deploy contracts to mainnet
- Update contract addresses in `app_config.dart`
- Update RPC URL to mainnet
- Update chain ID to 1

## File Structure Reference

```
lib/
├── config/
│   ├── app_config.dart          # ⚠️ ADD YOUR API KEYS HERE
│   └── contract_config.dart     # Contract ABIs
├── models/                       # Data models
├── services/                     # Business logic
├── screens/                      # UI screens
└── main.dart                    # App entry point
```

## Next Steps

1. ✅ Configure API keys
2. ✅ Register as manufacturer
3. ✅ Test with small batch
4. ⏳ Implement QR code viewer/export (optional enhancement)
5. ⏳ Add batch search/filter (optional enhancement)
6. ⏳ Deploy to production

## Support

- Documentation: See `README_APP.md`
- Smart Contracts: See `context/PharmaChain/README.md`
- Integration Guide: See `context/PharmaChain/MOBILE_APP_INTEGRATION_GUIDE.md`

Good luck with your MediChain deployment! 🚀
