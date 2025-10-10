// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title StudentRecords
 * @dev Smart contract for immutable student record verification
 * Stores cryptographic hashes of student records for verification
 */
contract StudentRecords {
    struct VerificationRecord {
        bytes32 documentHash;
        address verifiedBy;
        uint256 timestamp;
        string recordType; // "transcript", "certificate", "verification"
        bool isActive;
    }
    
    struct Student {
        string studentId;
        address owner;
        bool exists;
        uint256 recordCount;
    }
    
    // Mapping from student ID to student data
    mapping(string => Student) public students;
    
    // Mapping from student ID to array of verification records
    mapping(string => VerificationRecord[]) public verificationHistory;
    
    // Mapping from document hash to student ID for reverse lookup
    mapping(bytes32 => string) public hashToStudentId;
    
    // Events for logging
    event StudentRegistered(string indexed studentId, address indexed owner);
    event RecordVerified(string indexed studentId, bytes32 indexed documentHash, address indexed verifiedBy, string recordType);
    event RecordRevoked(string indexed studentId, bytes32 indexed documentHash, address indexed revokedBy);
    
    modifier onlyStudentOwner(string memory studentId) {
        require(students[studentId].exists, "Student does not exist");
        require(students[studentId].owner == msg.sender, "Not authorized for this student");
        _;
    }
    
    modifier studentExists(string memory studentId) {
        require(students[studentId].exists, "Student does not exist");
        _;
    }
    
    /**
     * @dev Register a new student
     * @param studentId Unique identifier for the student
     * @param studentOwner Address that will own this student's records
     */
    function registerStudent(string memory studentId, address studentOwner) public {
        require(!students[studentId].exists, "Student already registered");
        require(bytes(studentId).length > 0, "Student ID cannot be empty");
        
        students[studentId] = Student({
            studentId: studentId,
            owner: studentOwner,
            exists: true,
            recordCount: 0
        });
        
        emit StudentRegistered(studentId, studentOwner);
    }
    
    /**
     * @dev Add a verification record for a student
     * @param studentId The student's unique identifier
     * @param documentHash SHA-256 hash of the document content
     * @param recordType Type of record being verified
     */
    function addVerificationRecord(
        string memory studentId,
        bytes32 documentHash,
        string memory recordType
    ) public studentExists(studentId) {
        require(documentHash != bytes32(0), "Document hash cannot be empty");
        require(bytes(recordType).length > 0, "Record type cannot be empty");
        
        // Check if this hash already exists for this student
        VerificationRecord[] storage records = verificationHistory[studentId];
        for (uint i = 0; i < records.length; i++) {
            require(records[i].documentHash != documentHash, "Document hash already exists");
        }
        
        // Add new verification record
        verificationHistory[studentId].push(VerificationRecord({
            documentHash: documentHash,
            verifiedBy: msg.sender,
            timestamp: block.timestamp,
            recordType: recordType,
            isActive: true
        }));
        
        // Update reverse lookup
        hashToStudentId[documentHash] = studentId;
        
        // Update student record count
        students[studentId].recordCount++;
        
        emit RecordVerified(studentId, documentHash, msg.sender, recordType);
    }
    
    /**
     * @dev Verify a document hash exists and is active
     * @param documentHash The hash to verify
     * @return exists Whether the hash exists
     * @return studentId The student ID associated with the hash
     * @return verifiedBy Who verified the record
     * @return timestamp When it was verified
     * @return recordType Type of record
     * @return isActive Whether the record is still active
     */
    function verifyDocument(bytes32 documentHash) public view returns (
        bool exists,
        string memory studentId,
        address verifiedBy,
        uint256 timestamp,
        string memory recordType,
        bool isActive
    ) {
        studentId = hashToStudentId[documentHash];
        
        if (bytes(studentId).length == 0) {
            return (false, "", address(0), 0, "", false);
        }
        
        VerificationRecord[] storage records = verificationHistory[studentId];
        for (uint i = 0; i < records.length; i++) {
            if (records[i].documentHash == documentHash) {
                return (
                    true,
                    studentId,
                    records[i].verifiedBy,
                    records[i].timestamp,
                    records[i].recordType,
                    records[i].isActive
                );
            }
        }
        
        return (false, "", address(0), 0, "", false);
    }
    
    /**
     * @dev Get all verification records for a student
     * @param studentId The student's unique identifier
     * @return Array of verification records
     */
    function getStudentRecords(string memory studentId) public view studentExists(studentId) returns (VerificationRecord[] memory) {
        return verificationHistory[studentId];
    }
    
    /**
     * @dev Get the latest verification record for a student
     * @param studentId The student's unique identifier
     */
    function getLatestRecord(string memory studentId) public view studentExists(studentId) returns (
        bytes32 documentHash,
        address verifiedBy,
        uint256 timestamp,
        string memory recordType,
        bool isActive
    ) {
        VerificationRecord[] storage records = verificationHistory[studentId];
        require(records.length > 0, "No records found for student");
        
        VerificationRecord storage latestRecord = records[records.length - 1];
        return (
            latestRecord.documentHash,
            latestRecord.verifiedBy,
            latestRecord.timestamp,
            latestRecord.recordType,
            latestRecord.isActive
        );
    }
    
    /**
     * @dev Revoke a verification record (mark as inactive)
     * @param studentId The student's unique identifier
     * @param documentHash The hash of the record to revoke
     */
    function revokeRecord(string memory studentId, bytes32 documentHash) public studentExists(studentId) {
        VerificationRecord[] storage records = verificationHistory[studentId];
        
        for (uint i = 0; i < records.length; i++) {
            if (records[i].documentHash == documentHash && records[i].isActive) {
                records[i].isActive = false;
                emit RecordRevoked(studentId, documentHash, msg.sender);
                return;
            }
        }
        
        revert("Record not found or already inactive");
    }
    
    /**
     * @dev Get student information
     * @param studentId The student's unique identifier
     */
    function getStudentInfo(string memory studentId) public view returns (
        string memory id,
        address owner,
        uint256 recordCount,
        bool exists
    ) {
        Student storage student = students[studentId];
        return (student.studentId, student.owner, student.recordCount, student.exists);
    }
    
    /**
     * @dev Get total number of records for a student
     * @param studentId The student's unique identifier
     */
    function getRecordCount(string memory studentId) public view studentExists(studentId) returns (uint256) {
        return students[studentId].recordCount;
    }
    
    /**
     * @dev Check if a student is registered
     * @param studentId The student's unique identifier
     */
    function isStudentRegistered(string memory studentId) public view returns (bool) {
        return students[studentId].exists;
    }
}