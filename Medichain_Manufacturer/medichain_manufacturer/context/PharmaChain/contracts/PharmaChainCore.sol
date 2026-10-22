// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PharmaChainCore
 * @author Team YANIZA
 * @notice Core medicine tracking - Manufacturer → Distributor → Pharmacy
 * @dev Optimized for deployment (under 24KB)
 */
contract PharmaChainCore {

    // ========== ENUMS ==========
    enum State { Manufactured, InTransit, AtDistributor, AtPharmacy, Dispensed, Flagged }
    enum Role { None, Manufacturer, Distributor, Pharmacy, Consumer, Regulator, Admin }
    enum FlagSeverity { Low, Medium, High, Critical }

    // ========== STRUCTS ==========
    struct Medicine {
        uint256 id;
        uint256 batchId;
        string ipfsHash;
        bytes32 contentHash;
        address currentOwner;
        address manufacturer;
        State status;
        uint256 transferCount;
        uint256 scanCount;
        uint256 flagCount;
        bool isFlagged;
    }

    struct Actor {
        Role role;
        string name;
        string location;
        bool isActive;
        uint256 reputationScore;
    }

    // ========== STATE ==========
    mapping(uint256 => Medicine) public medicines;
    mapping(uint256 => address[]) public custodyHistory;
    mapping(uint256 => uint256[]) public timestampHistory;
    mapping(uint256 => bool) public isMedicineRegistered;
    
    mapping(address => Actor) public actors;
    mapping(address => bool) public isWhitelisted;
    
    address public admin;
    bool public paused;
    uint256 public totalMedicines;
    
    uint256 public constant MAX_TRANSFERS = 100;

    // ========== EVENTS ==========
    event MedicineRegistered(uint256 indexed id, uint256 indexed batchId, address indexed manufacturer, bytes32 contentHash, uint256 timestamp);
    event CustodyTransferred(uint256 indexed id, address indexed from, address indexed to, State newStatus, uint256 timestamp);
    event ActorRegistered(address indexed actor, Role role, uint256 timestamp);
    event DrugFlagged(uint256 indexed id, address indexed flagger, FlagSeverity severity, uint256 timestamp);
    event ContractPaused(address indexed by, uint256 timestamp);
    event ContractUnpaused(address indexed by, uint256 timestamp);

    // ========== MODIFIERS ==========
    modifier onlyAdmin() { require(msg.sender == admin, "!admin"); _; }
    modifier onlyRole(Role _r) { require(actors[msg.sender].role == _r, "!role"); _; }
    modifier whenNotPaused() { require(!paused, "paused"); _; }
    modifier medExists(uint256 _id) { require(isMedicineRegistered[_id], "!med"); _; }
    modifier onlyOwner(uint256 _id) { require(medicines[_id].currentOwner == msg.sender, "!owner"); _; }

    // ========== CONSTRUCTOR ==========
    constructor() {
        admin = msg.sender;
        actors[msg.sender] = Actor(Role.Admin, "Admin", "System", true, 1000);
        isWhitelisted[msg.sender] = true;
    }

    // ========== ADMIN ==========
    function registerActor(address _actor, Role _role, string calldata _name, string calldata _location) external onlyAdmin {
        require(_role != Role.None && _role != Role.Admin, "!role");
        require(actors[_actor].role == Role.None, "exists");
        actors[_actor] = Actor(_role, _name, _location, true, 500);
        isWhitelisted[_actor] = true;
        emit ActorRegistered(_actor, _role, block.timestamp);
    }

    function setActorStatus(address _actor, bool _active) external onlyAdmin {
        actors[_actor].isActive = _active;
        isWhitelisted[_actor] = _active;
    }

    function pause() external onlyAdmin { paused = true; emit ContractPaused(msg.sender, block.timestamp); }
    function unpause() external onlyAdmin { paused = false; emit ContractUnpaused(msg.sender, block.timestamp); }

    // ========== MEDICINE REGISTRATION ==========
    function registerMedicine(uint256 _id, uint256 _batchId, string calldata _ipfsHash, bytes32 _contentHash) 
        external whenNotPaused onlyRole(Role.Manufacturer) 
    {
        require(!isMedicineRegistered[_id], "exists");
        
        medicines[_id] = Medicine({
            id: _id,
            batchId: _batchId,
            ipfsHash: _ipfsHash,
            contentHash: _contentHash,
            currentOwner: msg.sender,
            manufacturer: msg.sender,
            status: State.Manufactured,
            transferCount: 0,
            scanCount: 0,
            flagCount: 0,
            isFlagged: false
        });
        
        custodyHistory[_id].push(msg.sender);
        timestampHistory[_id].push(block.timestamp);
        isMedicineRegistered[_id] = true;
        totalMedicines++;
        
        emit MedicineRegistered(_id, _batchId, msg.sender, _contentHash, block.timestamp);
    }

    function registerMedicineBatch(
        uint256[] calldata _ids, 
        uint256 _batchId, 
        string[] calldata _ipfsHashes, 
        bytes32[] calldata _contentHashes
    ) external whenNotPaused onlyRole(Role.Manufacturer) {
        require(_ids.length == _ipfsHashes.length && _ids.length == _contentHashes.length, "!len");
        require(_ids.length <= 50, "!max");
        
        for (uint256 i = 0; i < _ids.length; i++) {
            if (!isMedicineRegistered[_ids[i]]) {
                medicines[_ids[i]] = Medicine({
                    id: _ids[i],
                    batchId: _batchId,
                    ipfsHash: _ipfsHashes[i],
                    contentHash: _contentHashes[i],
                    currentOwner: msg.sender,
                    manufacturer: msg.sender,
                    status: State.Manufactured,
                    transferCount: 0,
                    scanCount: 0,
                    flagCount: 0,
                    isFlagged: false
                });
                custodyHistory[_ids[i]].push(msg.sender);
                timestampHistory[_ids[i]].push(block.timestamp);
                isMedicineRegistered[_ids[i]] = true;
                totalMedicines++;
                emit MedicineRegistered(_ids[i], _batchId, msg.sender, _contentHashes[i], block.timestamp);
            }
        }
    }

    // ========== CUSTODY TRANSFER ==========
    function transferCustody(uint256 _id, address _to) 
        external whenNotPaused medExists(_id) onlyOwner(_id) 
    {
        require(isWhitelisted[_to] && actors[_to].isActive, "!whitelisted");
        require(medicines[_id].transferCount < MAX_TRANSFERS, "!maxTx");
        
        Role fromRole = actors[msg.sender].role;
        Role toRole = actors[_to].role;
        
        // Validate flow
        if (fromRole == Role.Manufacturer) {
            require(toRole == Role.Distributor, "!flow");
        } else if (fromRole == Role.Distributor) {
            require(toRole == Role.Distributor || toRole == Role.Pharmacy, "!flow");
        } else if (fromRole == Role.Pharmacy) {
            require(toRole == Role.Consumer, "!flow");
        }
        
        medicines[_id].currentOwner = _to;
        medicines[_id].transferCount++;
        
        // Update status
        if (toRole == Role.Distributor) medicines[_id].status = State.AtDistributor;
        else if (toRole == Role.Pharmacy) medicines[_id].status = State.AtPharmacy;
        else if (toRole == Role.Consumer) medicines[_id].status = State.Dispensed;
        else medicines[_id].status = State.InTransit;
        
        custodyHistory[_id].push(_to);
        timestampHistory[_id].push(block.timestamp);
        
        emit CustodyTransferred(_id, msg.sender, _to, medicines[_id].status, block.timestamp);
    }

    function transferBatch(uint256[] calldata _ids, address _to) external whenNotPaused {
        require(isWhitelisted[_to] && actors[_to].isActive, "!whitelisted");
        for (uint256 i = 0; i < _ids.length; i++) {
            if (medicines[_ids[i]].currentOwner == msg.sender) {
                medicines[_ids[i]].currentOwner = _to;
                medicines[_ids[i]].transferCount++;
                custodyHistory[_ids[i]].push(_to);
                timestampHistory[_ids[i]].push(block.timestamp);
                
                Role toRole = actors[_to].role;
                if (toRole == Role.Distributor) medicines[_ids[i]].status = State.AtDistributor;
                else if (toRole == Role.Pharmacy) medicines[_ids[i]].status = State.AtPharmacy;
                
                emit CustodyTransferred(_ids[i], msg.sender, _to, medicines[_ids[i]].status, block.timestamp);
            }
        }
    }

    // ========== FLAGGING ==========
    function flagDrug(uint256 _id, FlagSeverity _severity) external whenNotPaused medExists(_id) {
        require(actors[msg.sender].role != Role.None, "!actor");
        
        medicines[_id].flagCount++;
        medicines[_id].isFlagged = true;
        if (_severity >= FlagSeverity.High) {
            medicines[_id].status = State.Flagged;
        }
        
        // Reduce reputation
        uint256 penalty = _severity == FlagSeverity.Critical ? 10 : 
                         _severity == FlagSeverity.High ? 5 : 
                         _severity == FlagSeverity.Medium ? 3 : 1;
        
        address[] memory history = custodyHistory[_id];
        for (uint256 i = 0; i < history.length; i++) {
            if (actors[history[i]].reputationScore > penalty) {
                actors[history[i]].reputationScore -= penalty;
            }
        }
        
        emit DrugFlagged(_id, msg.sender, _severity, block.timestamp);
    }

    function resolveFlag(uint256 _id) external medExists(_id) {
        require(actors[msg.sender].role == Role.Admin || actors[msg.sender].role == Role.Regulator, "!auth");
        medicines[_id].isFlagged = false;
        if (medicines[_id].status == State.Flagged) {
            medicines[_id].status = State.InTransit;
        }
    }

    // ========== VERIFICATION ==========
    function verifyHash(uint256 _id, bytes32 _hash) external view medExists(_id) returns (bool) {
        return medicines[_id].contentHash == _hash;
    }

    function verifySignature(uint256 _id, bytes32 _hash, bytes memory _sig) external view medExists(_id) returns (bool) {
        if (medicines[_id].contentHash != _hash) return false;
        
        bytes32 ethHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", _hash));
        (bytes32 r, bytes32 s, uint8 v) = _splitSig(_sig);
        address signer = ecrecover(ethHash, v, r, s);
        
        return signer == medicines[_id].manufacturer;
    }

    function _splitSig(bytes memory _sig) internal pure returns (bytes32 r, bytes32 s, uint8 v) {
        require(_sig.length == 65, "!sig");
        assembly {
            r := mload(add(_sig, 32))
            s := mload(add(_sig, 64))
            v := byte(0, mload(add(_sig, 96)))
        }
        if (v < 27) v += 27;
    }

    // ========== VIEW ==========
    function getCustodyHistory(uint256 _id) external view returns (address[] memory, uint256[] memory) {
        return (custodyHistory[_id], timestampHistory[_id]);
    }

    function getActorRole(address _actor) external view returns (Role) {
        return actors[_actor].role;
    }
}
