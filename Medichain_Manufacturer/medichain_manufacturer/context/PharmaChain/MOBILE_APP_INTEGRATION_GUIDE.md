# 🏥 PharmaChain: Advanced Mobile Integration & RBAC Blueprint

This guide details the internal logic, security permissions, and feature priorities for the PharmaChain mobile ecosystem (Flutter).

---

## � Part 0: Deliverables (What we are giving you)

To integrate the mobile app, you have been provided with the following technical artifacts:

1.  **Contract ABIs:** JSON files located in `artifacts/contracts/`.
    *   `PharmaChainCore.json`: Main tracking logic.
    *   `PharmaChainScanner.json`: GPS/Scan logging.
    *   `PharmaChainBatch.json`: Batch management.
2.  **Contract Addresses:** {
  "network": "sepolia",
  "deployedAt": "2026-02-13T06:01:26.997Z",
  "contracts": {
    "PharmaChainCore": "0x42b07481379ce4beF2aC70BC0329bD29a2E7cb8A",
    "PharmaChainScanner": "0x710a91E26754c126C3A1b8C0E0c5b06568d85493",
    "PharmaChainBatch": "0x555d8aFe7FD29eC64D84e930b1Bf0265D1cC68A8"
  }
}
3.  **Network Configuration:** 
    *   **Network:** Ethereum Sepolia Testnet
    *   **Chain ID:** `11155111`
    *   **RPC URL:** https://eth-sepolia.g.alchemy.com/v2/PGzZq8hP9sz-VFBVCNsW2
4.  **IPFS Gateway:** `https://gateway.pinata.cloud/ipfs/`

---

## �🔐 Part 1: Role-Based Access Control (RBAC) Architecture

The system uses a strict "Whitelist + Role" mechanism. An account cannot perform any supply chain action until it is registered in the `PharmaChainCore` contract by an Admin.

### Role Hierarchy & Priority

| Role | ID | Priority | Responsibility | Key Contract Functions |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | 6 | 🟢 CRITICAL | Onboarding & Security | `registerActor`, `deactivateActor`, `pause` |
| **Manufacturer**| 1 | 🔴 HIGH | Drug Origin & Batching | `registerMedicine`, `createBatch`, `registerMedicineInBatch` |
| **Regulator** | 5 | 🔴 HIGH | Compliance & Safety | `flagDrug`, `resolveFlag`, `reputationUpdate` |
| **Distributor** | 2 | 🟡 MEDIUM | Large Scale Logistics | `transferCustody`, `transferBatch`, `logScan` |
| **Pharmacy** | 3 | 🟡 MEDIUM | Retail Handling | `transferCustody`, `logScan` |
| **Consumer** | 4 | 🔵 LOW | Verification | `viewMedicine`, `flagDrug` (Reporting) |

---

## 🛠️ Part 2: Feature Breakdown by Role

### 1. The Manufacturer App (The Origin)
*   **Priority:** Ensure zero errors during data entry.
*   **Unique Feature: Batch Minting.** Ability to register 1,000+ items at once using the `Batch` contract.
*   **Data Integrity:** The app must automatically calculate the **SHA-256 hash** of the medicine details before sending them to IPFS to ensure the `contentHash` on the blockchain is 100% accurate.

### 2. The Logistics App (Distributor & Pharmacy)
*   **Priority:** Speed and Geo-Accuracy.
*   **Feature: Automated Scanning.** Users scan a palette (Batch ID) rather than 500 individual bottles.
*   **Feature: Geo-Fencing.** The app should check if the phone's GPS matches the "Location" string sent to the blockchain to prevent spoofing.

### 3. The Regulator Dashboard
*   **Priority:** Anomaly Detection.
*   **Feature: Reputation Scoring.** View the `reputationScore` of manufacturers. If a manufacturer has many flagged items, the regulator app should highlight them in Red.
*   **Feature: Emergency Flagging.** Instantly change a drug's status to "Flagged" globally if a counterfeit is detected.

### 4. The Consumer App (Public)
*   **Priority:** Ease of Use (No Wallet Required).
*   **Feature: Zero-Knowledge Verification.** The app uses a generic RPC provider (Infura/Alchemy) to read data so the user doesn't need to pay gas or have a Metamask account.

---

## 📜 Part 3: Technical Implementation Details (Flutter)

### Workflow of a "Scan & Verify" (Detailed)

1.  **Input:** `qrData = "762412"` (Standard QR scan).
2.  **Contract Call:** `core.medicines(762412)`
    *   *Result:* `(uint256 id, uint256 batchId, string ipfsHash, bytes32 contentHash, address currentOwner, State status...)`
3.  **App Logic:** 
    *   If `status == 5 (Flagged)`, immediately show a **DANGER** screen.
    *   If `status == 4 (Dispensed)`, show a warning: "This medicine has already been sold."
4.  **IPFS Fetch:**
    ```dart
    final response = await http.get(Uri.parse('https://ipfs.io/ipfs/$ipfsHash'));
    final jsonData = json.decode(response.body);
    ```
5.  **Cryptographic Check:**
    ```dart
    var bytes = utf8.encode(response.body); 
    var digest = sha256.convert(bytes);
    if (digest.toString() == contentHashFromBlockchain) {
      // ✅ SUCCESS
    }
    ```

---

## 🚀 Part 4: Integration Checklist for the Dev Team

1.  **Environment Setup:**
    *   Install `flutter_web3` or `web3dart`.
    *   Configure `AndroidManifest.xml` for Camera and GPS permissions.
2.  **The "Admin" Problem:**
    *   Remind devs that for testing, the **Admin** must register their test wallet addresses.
    *   Function: `core.registerActor(wallet_address, role_id, "Name", "Location")`.
3.  **IPFS Provider:**
    *   Advise using a dedicated **Pinata Gateway** URL for faster image and JSON loading.
4.  **Error Handling:**
    *   Handle "Insufficient Funds" (Gas) for write operations.
    *   Handle "Network Timeout" for blockchain nodes.
