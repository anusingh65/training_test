/**
 * PharmaChain - Hash Utility
 * ==========================
 * Generate and verify content hashes for medicine metadata
 * Uses keccak256 (same as Solidity) for blockchain compatibility
 * 
 * Usage:
 *   const { generateContentHash, verifyContentHash } = require('./utils/hash');
 *   const hash = generateContentHash(metadata);
 *   const isValid = verifyContentHash(metadata, onChainHash);
 */

const { ethers } = require('ethers');

/**
 * Normalize metadata object for consistent hashing
 * - Sorts keys alphabetically
 * - Removes undefined/null values
 * - Ensures consistent JSON stringification
 * 
 * @param {Object} metadata - Raw metadata object
 * @returns {Object} Normalized metadata
 */
function normalizeMetadata(metadata) {
    // Remove fields that shouldn't affect hash
    const excludeFields = ['uploaded_at', 'schema_version', 'ipfs_hash'];
    
    const normalize = (obj) => {
        if (obj === null || obj === undefined) {
            return null;
        }
        
        if (Array.isArray(obj)) {
            return obj.map(normalize).filter(x => x !== null);
        }
        
        if (typeof obj === 'object') {
            const sorted = {};
            Object.keys(obj)
                .filter(key => !excludeFields.includes(key))
                .sort()
                .forEach(key => {
                    const value = normalize(obj[key]);
                    if (value !== null && value !== undefined) {
                        sorted[key] = value;
                    }
                });
            return sorted;
        }
        
        // Convert numbers to strings for consistency
        if (typeof obj === 'number') {
            return String(obj);
        }
        
        return obj;
    };
    
    return normalize(metadata);
}

/**
 * Generate keccak256 hash of metadata
 * This hash is stored on-chain for verification
 * 
 * @param {Object} metadata - Medicine metadata object
 * @returns {string} bytes32 hash (0x prefixed)
 * 
 * @example
 * const hash = generateContentHash({
 *     medicine_id: 12345,
 *     name: "Paracetamol 500mg",
 *     batch_number: "BATCH-2024-001"
 * });
 * // Returns: "0x7d3a8f2b1c9e4d5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a"
 */
function generateContentHash(metadata) {
    if (!metadata || typeof metadata !== 'object') {
        throw new Error('Metadata must be an object');
    }

    // Normalize for consistent hashing
    const normalized = normalizeMetadata(metadata);
    
    // Convert to JSON string
    const jsonString = JSON.stringify(normalized);
    
    // Generate keccak256 hash (same as Solidity)
    const hash = ethers.keccak256(ethers.toUtf8Bytes(jsonString));
    
    return hash;
}

/**
 * Verify metadata against on-chain hash
 * 
 * @param {Object} metadata - Metadata fetched from IPFS
 * @param {string} onChainHash - Hash stored on blockchain
 * @returns {boolean} True if hashes match
 * 
 * @example
 * const isValid = verifyContentHash(fetchedMetadata, "0x7d3a8f2b...");
 * if (!isValid) {
 *     console.log("WARNING: Metadata has been tampered!");
 * }
 */
function verifyContentHash(metadata, onChainHash) {
    if (!onChainHash || !onChainHash.startsWith('0x')) {
        throw new Error('Invalid on-chain hash format');
    }

    const computedHash = generateContentHash(metadata);
    
    return computedHash.toLowerCase() === onChainHash.toLowerCase();
}

/**
 * Generate hash for batch metadata
 * 
 * @param {Object} batchMetadata - Batch metadata
 * @returns {string} bytes32 hash
 */
function generateBatchHash(batchMetadata) {
    return generateContentHash(batchMetadata);
}

/**
 * Create a complete medicine metadata object with hash
 * 
 * @param {Object} params - Medicine parameters
 * @returns {Object} Complete metadata with content hash
 * 
 * @example
 * const { metadata, contentHash, jsonString } = createMedicineMetadata({
 *     medicine_id: 12345,
 *     name: "Paracetamol 500mg",
 *     generic_name: "Acetaminophen",
 *     batch_number: "BATCH-2024-001",
 *     manufacture_date: "2024-01-15",
 *     expiry_date: "2026-01-15",
 *     manufacturer_name: "Cipla Ltd",
 *     manufacturer_license: "MFG-MH-001234",
 *     manufacturer_location: "Mumbai, Maharashtra",
 *     dosage: "500mg",
 *     form: "Tablet",
 *     pack_size: 10,
 *     mrp: 25.50,
 *     composition: ["Paracetamol IP 500mg"],
 *     storage: "Store below 25°C"
 * });
 */
function createMedicineMetadata(params) {
    // Validate required fields
    const required = ['medicine_id', 'name', 'batch_number', 'manufacture_date', 'expiry_date'];
    for (const field of required) {
        if (!params[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }

    // Build structured metadata
    const metadata = {
        medicine_id: params.medicine_id,
        name: params.name,
        generic_name: params.generic_name || null,
        batch_number: params.batch_number,
        manufacture_date: params.manufacture_date,
        expiry_date: params.expiry_date,
        manufacturer: {
            name: params.manufacturer_name || 'Unknown',
            license: params.manufacturer_license || null,
            location: params.manufacturer_location || null
        },
        dosage: params.dosage || null,
        form: params.form || null,
        pack_size: params.pack_size || null,
        mrp: params.mrp || null,
        composition: params.composition || [],
        storage: params.storage || null,
        warnings: params.warnings || [],
        category: params.category || null
    };

    // Remove null values for cleaner JSON
    const cleanMetadata = JSON.parse(JSON.stringify(metadata, (key, value) => {
        if (value === null || (Array.isArray(value) && value.length === 0)) {
            return undefined;
        }
        return value;
    }));

    // Generate content hash
    const contentHash = generateContentHash(cleanMetadata);
    
    return {
        metadata: cleanMetadata,
        contentHash: contentHash,
        jsonString: JSON.stringify(cleanMetadata, null, 2)
    };
}

/**
 * Create batch metadata with hash
 * 
 * @param {Object} params - Batch parameters
 * @returns {Object} Complete batch metadata with hash
 */
function createBatchMetadata(params) {
    const required = ['batch_id', 'batch_number', 'total_units', 'manufacture_date'];
    for (const field of required) {
        if (!params[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }

    const metadata = {
        batch_id: params.batch_id,
        batch_number: params.batch_number,
        total_units: params.total_units,
        manufacture_date: params.manufacture_date,
        expiry_date: params.expiry_date,
        manufacturer: {
            name: params.manufacturer_name,
            license: params.manufacturer_license,
            location: params.manufacturer_location
        },
        product_name: params.product_name,
        product_category: params.product_category
    };

    const contentHash = generateContentHash(metadata);

    return {
        metadata,
        contentHash,
        jsonString: JSON.stringify(metadata, null, 2)
    };
}

/**
 * Hash a simple string (for testing)
 * 
 * @param {string} str - String to hash
 * @returns {string} keccak256 hash
 */
function hashString(str) {
    return ethers.keccak256(ethers.toUtf8Bytes(str));
}

/**
 * Convert hash to bytes32 format for Solidity
 * 
 * @param {string} hash - Hash string
 * @returns {string} Properly formatted bytes32
 */
function toBytes32(hash) {
    if (!hash.startsWith('0x')) {
        hash = '0x' + hash;
    }
    // Ensure it's 66 characters (0x + 64 hex chars)
    if (hash.length !== 66) {
        throw new Error('Invalid hash length for bytes32');
    }
    return hash;
}

/**
 * Generate a deterministic medicine ID from batch + sequence
 * 
 * @param {string} batchNumber - Batch number
 * @param {number} sequence - Sequence within batch
 * @returns {number} Medicine ID (uint256 compatible)
 */
function generateMedicineId(batchNumber, sequence) {
    const combined = `${batchNumber}-${sequence}`;
    const hash = ethers.keccak256(ethers.toUtf8Bytes(combined));
    // Take first 8 bytes and convert to number
    const id = BigInt(hash.slice(0, 18));
    return Number(id % BigInt(2 ** 48));  // Keep it manageable size
}

/**
 * Demo: Show hash generation process
 */
function demonstrateHashing() {
    console.log('\n=== PharmaChain Hash Demonstration ===\n');

    const sampleMetadata = {
        medicine_id: 12345,
        name: "Paracetamol 500mg",
        batch_number: "BATCH-2024-001",
        manufacture_date: "2024-01-15",
        expiry_date: "2026-01-15",
        manufacturer: {
            name: "Cipla Ltd",
            license: "MFG-MH-001234"
        }
    };

    console.log('1. Original Metadata:');
    console.log(JSON.stringify(sampleMetadata, null, 2));

    console.log('\n2. Normalized (sorted keys):');
    const normalized = normalizeMetadata(sampleMetadata);
    console.log(JSON.stringify(normalized, null, 2));

    console.log('\n3. JSON String for hashing:');
    const jsonStr = JSON.stringify(normalized);
    console.log(jsonStr);

    console.log('\n4. Keccak256 Hash:');
    const hash = generateContentHash(sampleMetadata);
    console.log(hash);

    console.log('\n5. Verification Test:');
    console.log(`   Same data: ${verifyContentHash(sampleMetadata, hash) ? '✅ VALID' : '❌ INVALID'}`);

    // Tampered data
    const tampered = { ...sampleMetadata, name: "Fake Medicine" };
    console.log(`   Tampered:  ${verifyContentHash(tampered, hash) ? '✅ VALID' : '❌ INVALID (Tamper detected!)'}`);

    console.log('\n=== End Demonstration ===\n');
}

// Export all functions
module.exports = {
    generateContentHash,
    verifyContentHash,
    generateBatchHash,
    createMedicineMetadata,
    createBatchMetadata,
    hashString,
    toBytes32,
    generateMedicineId,
    normalizeMetadata,
    demonstrateHashing
};
