/**
 * PharmaChain Utilities
 * ======================
 * Export all utilities for easy importing
 * 
 * Usage:
 *   const pharmachain = require('pharmachain-utils');
 *   
 *   // IPFS functions
 *   const ipfsHash = await pharmachain.uploadMedicineMetadata(metadata);
 *   const data = await pharmachain.fetchFromIPFS(ipfsHash);
 *   
 *   // Hash functions
 *   const hash = pharmachain.generateContentHash(metadata);
 *   const isValid = pharmachain.verifyContentHash(data, hash);
 */

const pinata = require('./pinata');
const hash = require('./hash');

module.exports = {
    // Pinata IPFS functions
    uploadMedicineMetadata: pinata.uploadMedicineMetadata,
    uploadBatchMetadata: pinata.uploadBatchMetadata,
    fetchFromIPFS: pinata.fetchFromIPFS,
    fetchFromIPFSWithFallback: pinata.fetchFromIPFSWithFallback,
    existsOnIPFS: pinata.existsOnIPFS,
    unpinFromIPFS: pinata.unpinFromIPFS,
    listPinnedMedicines: pinata.listPinnedMedicines,
    testPinataConnection: pinata.testConnection,
    getIPFSUrl: pinata.getIPFSUrl,
    PINATA_GATEWAY: pinata.PINATA_GATEWAY,

    // Hash functions
    generateContentHash: hash.generateContentHash,
    verifyContentHash: hash.verifyContentHash,
    generateBatchHash: hash.generateBatchHash,
    createMedicineMetadata: hash.createMedicineMetadata,
    createBatchMetadata: hash.createBatchMetadata,
    hashString: hash.hashString,
    toBytes32: hash.toBytes32,
    generateMedicineId: hash.generateMedicineId,
    normalizeMetadata: hash.normalizeMetadata,
    demonstrateHashing: hash.demonstrateHashing
};
