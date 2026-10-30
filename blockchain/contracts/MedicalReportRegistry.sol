// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MedicalReportRegistry
 * @dev Cryptographic integrity registry for medical report SHA-256 hashes.
 * STRICT SECURITY POLICY:
 * - NO Patient Personally Identifiable Information (PII) is stored on-chain.
 * - NO medical parameters, lab values, or diagnoses are stored on-chain.
 * - ONLY non-identifying SHA-256 digests and report UUID strings are anchored.
 */
contract MedicalReportRegistry {
    address public immutable owner;

    struct ReportRecord {
        bytes32 fileHashSha256;
        uint256 registeredAt;
        bool exists;
    }

    // Mapping from reportUUID string -> ReportRecord
    mapping(string => ReportRecord) private reports;

    // Events for immutable on-chain audit trails
    event ReportHashRegistered(
        string indexed reportUUID,
        bytes32 indexed fileHashSha256,
        uint256 timestamp,
        address indexed registrar
    );

    event ReportVerificationAttempted(
        string indexed reportUUID,
        bool isMatch,
        uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only registry contract owner may execute");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Registers a new medical report SHA-256 hash
     * @param reportUUID Non-identifying UUID of the report
     * @param fileHashSha256 32-byte cryptographic SHA-256 digest of original PDF/image
     */
    function registerReportHash(
        string calldata reportUUID,
        bytes32 fileHashSha256
    ) external {
        require(bytes(reportUUID).length > 0, "Report UUID cannot be empty");
        require(fileHashSha256 != bytes32(0), "Report SHA-256 hash cannot be zero");
        require(!reports[reportUUID].exists, "Report hash is already registered on blockchain");

        reports[reportUUID] = ReportRecord({
            fileHashSha256: fileHashSha256,
            registeredAt: block.timestamp,
            exists: true
        });

        emit ReportHashRegistered(reportUUID, fileHashSha256, block.timestamp, msg.sender);
    }

    /**
     * @notice Verifies whether a given SHA-256 hash matches the on-chain recorded digest
     * @param reportUUID The UUID reference of the report
     * @param submittedHash The SHA-256 hash recomputed from the current file
     * @return isMatch True if submitted hash exactly equals registered hash, False otherwise
     * @return registeredAt Unix timestamp of original on-chain registration
     */
    function verifyReportIntegrity(
        string calldata reportUUID,
        bytes32 submittedHash
    ) external returns (bool isMatch, uint256 registeredAt) {
        ReportRecord memory record = reports[reportUUID];
        if (!record.exists) {
            emit ReportVerificationAttempted(reportUUID, false, block.timestamp);
            return (false, 0);
        }

        bool matchResult = (record.fileHashSha256 == submittedHash);
        emit ReportVerificationAttempted(reportUUID, matchResult, block.timestamp);
        return (matchResult, record.registeredAt);
    }

    /**
     * @notice Read-only inspection of registration metadata
     * @param reportUUID The UUID reference of the report
     */
    function getReportRecord(
        string calldata reportUUID
    ) external view returns (bytes32 fileHashSha256, uint256 registeredAt, bool exists) {
        ReportRecord memory record = reports[reportUUID];
        return (record.fileHashSha256, record.registeredAt, record.exists);
    }
}
