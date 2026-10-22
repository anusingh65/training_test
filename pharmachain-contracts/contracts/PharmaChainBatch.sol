// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PharmaChainBatch
 * @author Team YANIZA
 * @notice Batch management module for PharmaChain
 * @dev Manages batches of medicines, links to Core for registration
 */

interface IPharmaChainCore {
    function registerMedicine(uint256 _id, uint256 _batchId, string calldata _ipfsHash, bytes32 _contentHash) external;
    function getActorRole(address _actor) external view returns (uint8);
    function isMedicineRegistered(uint256 _id) external view returns (bool);
}

contract PharmaChainBatch {

    // ========== STRUCTS ==========
    struct Batch {
        uint256 id;
        string batchNumber;
        string ipfsHash;
        bytes32 contentHash;
        address manufacturer;
        uint256 totalUnits;
        uint256 registeredUnits;
        uint256 createdAt;
        bool isComplete;
    }

    // ========== STATE ==========
    IPharmaChainCore public coreContract;
    address public admin;
    
    mapping(uint256 => Batch) public batches;
    mapping(uint256 => uint256[]) public batchMedicines;
    mapping(uint256 => bool) public isBatchRegistered;
    mapping(address => uint256[]) public manufacturerBatches;
    
    uint256 public totalBatches;
    uint256 public constant MAX_BATCH_SIZE = 10000;

    // ========== EVENTS ==========
    event BatchCreated(
        uint256 indexed batchId,
        address indexed manufacturer,
        string batchNumber,
        uint256 totalUnits,
        uint256 timestamp
    );

    event BatchCompleted(
        uint256 indexed batchId,
        uint256 totalUnits,
        uint256 timestamp
    );

    event MedicineAddedToBatch(
        uint256 indexed batchId,
        uint256 indexed medicineId,
        uint256 indexInBatch,
        uint256 timestamp
    );

    // ========== CONSTRUCTOR ==========
    constructor(address _coreContract) {
        coreContract = IPharmaChainCore(_coreContract);
        admin = msg.sender;
    }

    // ========== ADMIN ==========
    function setCoreContract(address _core) external {
        require(msg.sender == admin, "!admin");
        coreContract = IPharmaChainCore(_core);
    }

    // ========== BATCH MANAGEMENT ==========

    /**
     * @notice Create a new batch
     */
    function createBatch(
        uint256 _batchId,
        string calldata _batchNumber,
        uint256 _totalUnits,
        string calldata _ipfsHash,
        bytes32 _contentHash
    ) external {
        require(coreContract.getActorRole(msg.sender) == 1, "!manufacturer"); // Role.Manufacturer = 1
        require(!isBatchRegistered[_batchId], "exists");
        require(_totalUnits > 0 && _totalUnits <= MAX_BATCH_SIZE, "!size");

        batches[_batchId] = Batch({
            id: _batchId,
            batchNumber: _batchNumber,
            ipfsHash: _ipfsHash,
            contentHash: _contentHash,
            manufacturer: msg.sender,
            totalUnits: _totalUnits,
            registeredUnits: 0,
            createdAt: block.timestamp,
            isComplete: false
        });

        isBatchRegistered[_batchId] = true;
        manufacturerBatches[msg.sender].push(_batchId);
        totalBatches++;

        emit BatchCreated(_batchId, msg.sender, _batchNumber, _totalUnits, block.timestamp);
    }

    /**
     * @notice Add a medicine to a batch (registers in Core too)
     */
    function addMedicineToBatch(
        uint256 _batchId,
        uint256 _medicineId,
        string calldata _ipfsHash,
        bytes32 _contentHash
    ) external {
        require(isBatchRegistered[_batchId], "!batch");
        require(batches[_batchId].manufacturer == msg.sender, "!owner");
        require(!batches[_batchId].isComplete, "complete");
        require(!coreContract.isMedicineRegistered(_medicineId), "med exists");

        // Register in core contract
        coreContract.registerMedicine(_medicineId, _batchId, _ipfsHash, _contentHash);

        // Add to batch tracking
        batchMedicines[_batchId].push(_medicineId);
        batches[_batchId].registeredUnits++;

        emit MedicineAddedToBatch(_batchId, _medicineId, batches[_batchId].registeredUnits, block.timestamp);

        // Check completion
        if (batches[_batchId].registeredUnits >= batches[_batchId].totalUnits) {
            batches[_batchId].isComplete = true;
            emit BatchCompleted(_batchId, batches[_batchId].registeredUnits, block.timestamp);
        }
    }

    /**
     * @notice Bulk add medicines to batch (when batch QR is scanned)
     */
    function addMedicinesToBatch(
        uint256 _batchId,
        uint256[] calldata _medicineIds,
        string[] calldata _ipfsHashes,
        bytes32[] calldata _contentHashes
    ) external {
        require(isBatchRegistered[_batchId], "!batch");
        require(batches[_batchId].manufacturer == msg.sender, "!owner");
        require(!batches[_batchId].isComplete, "complete");
        require(_medicineIds.length == _ipfsHashes.length, "!len");
        require(_medicineIds.length == _contentHashes.length, "!len");
        require(_medicineIds.length <= 100, "!max");

        uint256 added = 0;
        for (uint256 i = 0; i < _medicineIds.length; i++) {
            if (!coreContract.isMedicineRegistered(_medicineIds[i])) {
                // This will fail if core contract doesn't allow external calls
                // In production, you'd use a different pattern
                try coreContract.registerMedicine(_medicineIds[i], _batchId, _ipfsHashes[i], _contentHashes[i]) {
                    batchMedicines[_batchId].push(_medicineIds[i]);
                    added++;
                    emit MedicineAddedToBatch(_batchId, _medicineIds[i], batches[_batchId].registeredUnits + added, block.timestamp);
                } catch {
                    // Skip if registration fails
                }
            }
        }

        batches[_batchId].registeredUnits += added;

        if (batches[_batchId].registeredUnits >= batches[_batchId].totalUnits) {
            batches[_batchId].isComplete = true;
            emit BatchCompleted(_batchId, batches[_batchId].registeredUnits, block.timestamp);
        }
    }

    /**
     * @notice Mark batch as complete manually
     */
    function completeBatch(uint256 _batchId) external {
        require(batches[_batchId].manufacturer == msg.sender, "!owner");
        batches[_batchId].isComplete = true;
        emit BatchCompleted(_batchId, batches[_batchId].registeredUnits, block.timestamp);
    }

    // ========== VIEW FUNCTIONS ==========

    function getBatch(uint256 _batchId) external view returns (
        string memory batchNumber,
        address manufacturer,
        uint256 totalUnits,
        uint256 registeredUnits,
        bool isComplete
    ) {
        Batch storage b = batches[_batchId];
        return (b.batchNumber, b.manufacturer, b.totalUnits, b.registeredUnits, b.isComplete);
    }

    function getBatchMedicines(uint256 _batchId) external view returns (uint256[] memory) {
        return batchMedicines[_batchId];
    }

    function getManufacturerBatches(address _manufacturer) external view returns (uint256[] memory) {
        return manufacturerBatches[_manufacturer];
    }

    function getBatchCount(uint256 _batchId) external view returns (uint256) {
        return batchMedicines[_batchId].length;
    }
}
