// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PharmaChainScanner
 * @author Team YANIZA
 * @notice Scan logging and AI anomaly detection module
 * @dev Links to PharmaChainCore for medicine validation
 */

interface IPharmaChainCore {
    function isMedicineRegistered(uint256 _id) external view returns (bool);
    function getActorRole(address _actor) external view returns (uint8);
}

contract PharmaChainScanner {

    // ========== STRUCTS ==========
    struct ScanRecord {
        address scanner;
        int256 latitude;    // * 1e6
        int256 longitude;   // * 1e6
        uint256 timestamp;
        string location;
        string deviceId;
    }

    // ========== STATE ==========
    IPharmaChainCore public coreContract;
    address public admin;
    
    mapping(uint256 => ScanRecord[]) public scanHistory;
    mapping(uint256 => uint256) public scanCount;
    mapping(address => uint256) public scannerTotalScans;
    
    uint256 public totalScans;
    uint256 public totalAlerts;
    
    // Velocity threshold: 1 hour
    uint256 public constant VELOCITY_THRESHOLD = 1 hours;

    // ========== EVENTS ==========
    event DrugScanned(
        uint256 indexed medicineId,
        address indexed scanner,
        int256 latitude,
        int256 longitude,
        uint256 scanNumber,
        uint256 timestamp
    );

    event VelocityAlert(
        uint256 indexed medicineId,
        address indexed scanner,
        string currentLocation,
        string previousLocation,
        uint256 timeDelta,
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

    // ========== SCANNING ==========
    
    /**
     * @notice Log a scan - Critical for AI anomaly detection
     * @param _medicineId Medicine being scanned
     * @param _latitude Latitude * 1e6 (e.g., 19283746 = 19.283746°)
     * @param _longitude Longitude * 1e6
     * @param _location Human-readable location
     * @param _deviceId Scanner device identifier
     */
    function logScan(
        uint256 _medicineId,
        int256 _latitude,
        int256 _longitude,
        string calldata _location,
        string calldata _deviceId
    ) external {
        require(coreContract.isMedicineRegistered(_medicineId), "!medicine");
        require(coreContract.getActorRole(msg.sender) != 0, "!registered");

        // Check for velocity anomaly
        uint256 currentScanCount = scanCount[_medicineId];
        if (currentScanCount > 0) {
            ScanRecord storage lastScan = scanHistory[_medicineId][currentScanCount - 1];
            uint256 timeDelta = block.timestamp - lastScan.timestamp;
            
            // If scanned in different location within threshold time
            if (timeDelta < VELOCITY_THRESHOLD) {
                if (lastScan.latitude != _latitude || lastScan.longitude != _longitude) {
                    totalAlerts++;
                    emit VelocityAlert(
                        _medicineId,
                        msg.sender,
                        _location,
                        lastScan.location,
                        timeDelta,
                        block.timestamp
                    );
                }
            }
        }

        // Record scan
        scanHistory[_medicineId].push(ScanRecord({
            scanner: msg.sender,
            latitude: _latitude,
            longitude: _longitude,
            timestamp: block.timestamp,
            location: _location,
            deviceId: _deviceId
        }));

        scanCount[_medicineId]++;
        scannerTotalScans[msg.sender]++;
        totalScans++;

        emit DrugScanned(
            _medicineId,
            msg.sender,
            _latitude,
            _longitude,
            scanCount[_medicineId],
            block.timestamp
        );
    }

    /**
     * @notice Batch scan multiple medicines at once
     */
    function logBatchScan(
        uint256[] calldata _medicineIds,
        int256 _latitude,
        int256 _longitude,
        string calldata _location,
        string calldata _deviceId
    ) external {
        require(_medicineIds.length <= 50, "!max");
        
        for (uint256 i = 0; i < _medicineIds.length; i++) {
            if (coreContract.isMedicineRegistered(_medicineIds[i])) {
                scanHistory[_medicineIds[i]].push(ScanRecord({
                    scanner: msg.sender,
                    latitude: _latitude,
                    longitude: _longitude,
                    timestamp: block.timestamp,
                    location: _location,
                    deviceId: _deviceId
                }));
                
                scanCount[_medicineIds[i]]++;
                totalScans++;
                
                emit DrugScanned(
                    _medicineIds[i],
                    msg.sender,
                    _latitude,
                    _longitude,
                    scanCount[_medicineIds[i]],
                    block.timestamp
                );
            }
        }
        scannerTotalScans[msg.sender] += _medicineIds.length;
    }

    // ========== VIEW FUNCTIONS ==========
    
    function getScanHistory(uint256 _medicineId) external view returns (ScanRecord[] memory) {
        return scanHistory[_medicineId];
    }

    function getLastScan(uint256 _medicineId) external view returns (
        address scanner,
        int256 latitude,
        int256 longitude,
        uint256 timestamp,
        string memory location
    ) {
        uint256 count = scanCount[_medicineId];
        require(count > 0, "!scans");
        ScanRecord storage scan = scanHistory[_medicineId][count - 1];
        return (scan.scanner, scan.latitude, scan.longitude, scan.timestamp, scan.location);
    }

    function getScanCount(uint256 _medicineId) external view returns (uint256) {
        return scanCount[_medicineId];
    }

    function getStats() external view returns (uint256 _totalScans, uint256 _totalAlerts) {
        return (totalScans, totalAlerts);
    }
}
