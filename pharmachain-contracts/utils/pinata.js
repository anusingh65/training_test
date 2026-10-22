/**
 * PharmaChain - Pinata IPFS Utility
 * ==================================
 * Upload and fetch medicine metadata from IPFS via Pinata
 * 
 * Usage:
 *   const { uploadMedicineMetadata, fetchFromIPFS } = require('./utils/pinata');
 *   const ipfsHash = await uploadMedicineMetadata(metadata);
 *   const data = await fetchFromIPFS(ipfsHash);
 */

const axios = require('axios');
require('dotenv').config();

// Pinata API endpoints
const PINATA_API_URL = 'https://api.pinata.cloud';
const PINATA_GATEWAY = 'https://gateway.pinata.cloud/ipfs';

// Get credentials from environment
const PINATA_API_KEY = process.env.PINATA_API_KEY;
const PINATA_SECRET_KEY = process.env.PINATA_SECRET_KEY;
const PINATA_JWT = process.env.PINATA_JWT;

/**
 * Validate that Pinata credentials are configured
 */
function validateCredentials() {
    if (!PINATA_JWT && (!PINATA_API_KEY || !PINATA_SECRET_KEY)) {
        throw new Error(
            'Pinata credentials not found!\n' +
            'Add to your .env file:\n' +
            '  PINATA_API_KEY=your_api_key\n' +
            '  PINATA_SECRET_KEY=your_secret_key\n' +
            '  PINATA_JWT=your_jwt_token'
        );
    }
}

/**
 * Get authorization headers for Pinata API
 */
function getHeaders() {
    if (PINATA_JWT) {
        return {
            'Authorization': `Bearer ${PINATA_JWT}`,
            'Content-Type': 'application/json'
        };
    }
    return {
        'pinata_api_key': PINATA_API_KEY,
        'pinata_secret_key': PINATA_SECRET_KEY,
        'Content-Type': 'application/json'
    };
}

/**
 * Upload medicine metadata to IPFS
 * 
 * @param {Object} metadata - Medicine metadata object
 * @param {number} metadata.medicine_id - Unique medicine ID
 * @param {string} metadata.name - Medicine name
 * @param {string} metadata.batch_number - Batch number
 * @param {string} metadata.manufacture_date - ISO date string
 * @param {string} metadata.expiry_date - ISO date string
 * @param {Object} metadata.manufacturer - Manufacturer details
 * @returns {Promise<string>} IPFS hash (CID)
 * 
 * @example
 * const ipfsHash = await uploadMedicineMetadata({
 *     medicine_id: 12345,
 *     name: "Paracetamol 500mg",
 *     batch_number: "BATCH-2024-001",
 *     manufacture_date: "2024-01-15",
 *     expiry_date: "2026-01-15",
 *     manufacturer: {
 *         name: "Cipla Ltd",
 *         license: "MFG-MH-001234",
 *         location: "Mumbai, Maharashtra"
 *     }
 * });
 */
async function uploadMedicineMetadata(metadata) {
    validateCredentials();

    // Validate required fields
    const requiredFields = ['medicine_id', 'name', 'batch_number'];
    for (const field of requiredFields) {
        if (!metadata[field]) {
            throw new Error(`Missing required field: ${field}`);
        }
    }

    // Add timestamp
    const dataToUpload = {
        ...metadata,
        uploaded_at: new Date().toISOString(),
        schema_version: "1.0"
    };

    try {
        const response = await axios.post(
            `${PINATA_API_URL}/pinning/pinJSONToIPFS`,
            {
                pinataContent: dataToUpload,
                pinataMetadata: {
                    name: `medicine-${metadata.medicine_id}`,
                    keyvalues: {
                        medicine_id: String(metadata.medicine_id),
                        batch_number: metadata.batch_number,
                        type: 'medicine_metadata'
                    }
                },
                pinataOptions: {
                    cidVersion: 0  // Use CIDv0 (starts with Qm...)
                }
            },
            { headers: getHeaders() }
        );

        console.log(`✅ Uploaded to IPFS: ${response.data.IpfsHash}`);
        console.log(`   View at: ${PINATA_GATEWAY}/${response.data.IpfsHash}`);
        
        return response.data.IpfsHash;

    } catch (error) {
        if (error.response) {
            throw new Error(`Pinata API error: ${error.response.data.error || error.response.statusText}`);
        }
        throw error;
    }
}

/**
 * Upload batch metadata to IPFS
 * 
 * @param {Object} batchMetadata - Batch metadata object
 * @returns {Promise<string>} IPFS hash (CID)
 */
async function uploadBatchMetadata(batchMetadata) {
    validateCredentials();

    const dataToUpload = {
        ...batchMetadata,
        uploaded_at: new Date().toISOString(),
        schema_version: "1.0",
        type: "batch"
    };

    try {
        const response = await axios.post(
            `${PINATA_API_URL}/pinning/pinJSONToIPFS`,
            {
                pinataContent: dataToUpload,
                pinataMetadata: {
                    name: `batch-${batchMetadata.batch_id}`,
                    keyvalues: {
                        batch_id: String(batchMetadata.batch_id),
                        batch_number: batchMetadata.batch_number,
                        type: 'batch_metadata'
                    }
                }
            },
            { headers: getHeaders() }
        );

        console.log(`✅ Batch uploaded to IPFS: ${response.data.IpfsHash}`);
        return response.data.IpfsHash;

    } catch (error) {
        if (error.response) {
            throw new Error(`Pinata API error: ${error.response.data.error || error.response.statusText}`);
        }
        throw error;
    }
}

/**
 * Fetch metadata from IPFS using hash
 * 
 * @param {string} ipfsHash - IPFS CID (e.g., "QmXyz...")
 * @returns {Promise<Object>} Parsed JSON metadata
 * 
 * @example
 * const metadata = await fetchFromIPFS("QmX7bVbPTLCKPdJqB7bGjFzenH5E8ST6NVSiC3KwUfX9Lz");
 */
async function fetchFromIPFS(ipfsHash) {
    if (!ipfsHash || ipfsHash.length < 10) {
        throw new Error('Invalid IPFS hash');
    }

    // Remove ipfs:// prefix if present
    const cleanHash = ipfsHash.replace('ipfs://', '').replace('/ipfs/', '');

    try {
        const response = await axios.get(
            `${PINATA_GATEWAY}/${cleanHash}`,
            { timeout: 30000 }  // 30 second timeout
        );

        return response.data;

    } catch (error) {
        if (error.code === 'ECONNABORTED') {
            throw new Error('IPFS fetch timeout - try again');
        }
        if (error.response?.status === 404) {
            throw new Error(`IPFS content not found: ${cleanHash}`);
        }
        throw error;
    }
}

/**
 * Fetch using alternative gateways (backup)
 */
async function fetchFromIPFSWithFallback(ipfsHash) {
    const gateways = [
        'https://gateway.pinata.cloud/ipfs',
        'https://ipfs.io/ipfs',
        'https://cloudflare-ipfs.com/ipfs',
        'https://dweb.link/ipfs'
    ];

    const cleanHash = ipfsHash.replace('ipfs://', '').replace('/ipfs/', '');

    for (const gateway of gateways) {
        try {
            const response = await axios.get(
                `${gateway}/${cleanHash}`,
                { timeout: 10000 }
            );
            console.log(`✅ Fetched from: ${gateway}`);
            return response.data;
        } catch (error) {
            console.log(`❌ Failed: ${gateway}`);
            continue;
        }
    }

    throw new Error('Failed to fetch from all IPFS gateways');
}

/**
 * Check if content exists on IPFS
 * 
 * @param {string} ipfsHash - IPFS CID
 * @returns {Promise<boolean>}
 */
async function existsOnIPFS(ipfsHash) {
    try {
        await axios.head(`${PINATA_GATEWAY}/${ipfsHash}`, { timeout: 5000 });
        return true;
    } catch {
        return false;
    }
}

/**
 * Unpin content from Pinata (delete)
 * 
 * @param {string} ipfsHash - IPFS CID to unpin
 * @returns {Promise<boolean>}
 */
async function unpinFromIPFS(ipfsHash) {
    validateCredentials();

    try {
        await axios.delete(
            `${PINATA_API_URL}/pinning/unpin/${ipfsHash}`,
            { headers: getHeaders() }
        );
        console.log(`✅ Unpinned: ${ipfsHash}`);
        return true;
    } catch (error) {
        console.error(`❌ Failed to unpin: ${error.message}`);
        return false;
    }
}

/**
 * List all pinned medicine metadata
 * 
 * @returns {Promise<Array>} List of pinned items
 */
async function listPinnedMedicines() {
    validateCredentials();

    try {
        const response = await axios.get(
            `${PINATA_API_URL}/data/pinList?metadata[keyvalues][type]={"value":"medicine_metadata","op":"eq"}`,
            { headers: getHeaders() }
        );

        return response.data.rows.map(row => ({
            ipfsHash: row.ipfs_pin_hash,
            medicine_id: row.metadata?.keyvalues?.medicine_id,
            batch_number: row.metadata?.keyvalues?.batch_number,
            pinned_at: row.date_pinned
        }));

    } catch (error) {
        throw new Error(`Failed to list pins: ${error.message}`);
    }
}

/**
 * Test Pinata connection
 */
async function testConnection() {
    validateCredentials();

    try {
        const response = await axios.get(
            `${PINATA_API_URL}/data/testAuthentication`,
            { headers: getHeaders() }
        );
        console.log('✅ Pinata connection successful!');
        console.log(`   Message: ${response.data.message}`);
        return true;
    } catch (error) {
        console.error('❌ Pinata connection failed:', error.message);
        return false;
    }
}

/**
 * Get IPFS gateway URL for a hash
 */
function getIPFSUrl(ipfsHash) {
    return `${PINATA_GATEWAY}/${ipfsHash}`;
}

// Export all functions
module.exports = {
    uploadMedicineMetadata,
    uploadBatchMetadata,
    fetchFromIPFS,
    fetchFromIPFSWithFallback,
    existsOnIPFS,
    unpinFromIPFS,
    listPinnedMedicines,
    testConnection,
    getIPFSUrl,
    PINATA_GATEWAY
};
