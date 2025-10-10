"""
Blockchain service for immutable student record verification
Handles interaction with Ethereum smart contracts and Web3
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from datetime import datetime, timezone
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class BlockchainService:
    """Service for interacting with student records smart contract"""
    
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.account = None
        self.contract_address = None
        self.is_connected = False
        
        # Load configuration
        self.rpc_url = os.getenv('BLOCKCHAIN_RPC_URL', 'http://localhost:8545')
        self.private_key = os.getenv('BLOCKCHAIN_PRIVATE_KEY')
        self.contract_address = os.getenv('BLOCKCHAIN_CONTRACT_ADDRESS')
        self.chain_id = int(os.getenv('BLOCKCHAIN_CHAIN_ID', '31337'))  # Default to Hardhat
        
        # Contract ABI (Application Binary Interface)
        self.contract_abi = [
            {
                "inputs": [
                    {"internalType": "string", "name": "studentId", "type": "string"},
                    {"internalType": "address", "name": "studentOwner", "type": "address"}
                ],
                "name": "registerStudent",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "string", "name": "studentId", "type": "string"},
                    {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
                    {"internalType": "string", "name": "recordType", "type": "string"}
                ],
                "name": "addVerificationRecord",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"}
                ],
                "name": "verifyDocument",
                "outputs": [
                    {"internalType": "bool", "name": "exists", "type": "bool"},
                    {"internalType": "string", "name": "studentId", "type": "string"},
                    {"internalType": "address", "name": "verifiedBy", "type": "address"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {"internalType": "string", "name": "recordType", "type": "string"},
                    {"internalType": "bool", "name": "isActive", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "string", "name": "studentId", "type": "string"}
                ],
                "name": "getStudentRecords",
                "outputs": [
                    {
                        "components": [
                            {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
                            {"internalType": "address", "name": "verifiedBy", "type": "address"},
                            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                            {"internalType": "string", "name": "recordType", "type": "string"},
                            {"internalType": "bool", "name": "isActive", "type": "bool"}
                        ],
                        "internalType": "struct StudentRecords.VerificationRecord[]",
                        "name": "",
                        "type": "tuple[]"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "string", "name": "studentId", "type": "string"}
                ],
                "name": "isStudentRegistered",
                "outputs": [
                    {"internalType": "bool", "name": "", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "internalType": "string", "name": "studentId", "type": "string"},
                    {"indexed": True, "internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
                    {"indexed": True, "internalType": "address", "name": "verifiedBy", "type": "address"},
                    {"indexed": False, "internalType": "string", "name": "recordType", "type": "string"}
                ],
                "name": "RecordVerified",
                "type": "event"
            }
        ]
        
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize Web3 connection and contract instance"""
        try:
            # Connect to Ethereum node
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add PoA middleware for test networks
            if self.chain_id != 1:  # Not mainnet
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection
            if not self.w3.is_connected():
                logger.error("Failed to connect to Ethereum node")
                return
            
            # Load account if private key is provided
            if self.private_key:
                try:
                    self.account = Account.from_key(self.private_key)
                    logger.info(f"Loaded account: {self.account.address}")
                except Exception as e:
                    logger.error(f"Failed to load account: {e}")
                    return
            
            # Initialize contract if address is provided
            if self.contract_address:
                try:
                    self.contract = self.w3.eth.contract(
                        address=self.contract_address,
                        abi=self.contract_abi
                    )
                    logger.info(f"Connected to contract at: {self.contract_address}")
                    self.is_connected = True
                except Exception as e:
                    logger.error(f"Failed to initialize contract: {e}")
            else:
                logger.warning("No contract address provided - blockchain features disabled")
        
        except Exception as e:
            logger.error(f"Failed to initialize blockchain connection: {e}")
    
    def generate_document_hash(self, content: str) -> str:
        """Generate SHA-256 hash of document content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _convert_to_bytes32(self, hex_string: str) -> bytes:
        """Convert hex string to bytes32"""
        if hex_string.startswith('0x'):
            hex_string = hex_string[2:]
        return bytes.fromhex(hex_string)
    
    async def register_student_on_chain(self, student_id: str, owner_address: Optional[str] = None) -> Dict[str, Any]:
        """Register a student on the blockchain"""
        if not self.is_connected:
            return {"success": False, "error": "Blockchain not connected"}
        
        try:
            # Use provided address or default to service account
            owner_addr = owner_address if owner_address else self.account.address
            
            # Check if student is already registered
            is_registered = self.contract.functions.isStudentRegistered(student_id).call()
            if is_registered:
                return {"success": False, "error": "Student already registered"}
            
            # Build transaction
            function_call = self.contract.functions.registerStudent(student_id, owner_addr)
            
            # Estimate gas
            gas_estimate = function_call.estimate_gas({'from': self.account.address})
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.account.address,
                'gas': gas_estimate + 10000,  # Add buffer
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': self.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": True,
                "transaction_hash": receipt.transactionHash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed
            }
        
        except Exception as e:
            logger.error(f"Failed to register student on blockchain: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_verification_record(
        self, 
        student_id: str, 
        document_content: str, 
        record_type: str = "transcript"
    ) -> Dict[str, Any]:
        """Add a verification record to the blockchain"""
        if not self.is_connected:
            return {"success": False, "error": "Blockchain not connected"}
        
        try:
            # Generate document hash
            doc_hash = self.generate_document_hash(document_content)
            doc_hash_bytes = self._convert_to_bytes32(doc_hash)
            
            # Check if student is registered
            is_registered = self.contract.functions.isStudentRegistered(student_id).call()
            if not is_registered:
                # Auto-register student
                register_result = await self.register_student_on_chain(student_id)
                if not register_result["success"]:
                    return register_result
            
            # Build transaction
            function_call = self.contract.functions.addVerificationRecord(
                student_id, doc_hash_bytes, record_type
            )
            
            # Estimate gas
            gas_estimate = function_call.estimate_gas({'from': self.account.address})
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.account.address,
                'gas': gas_estimate + 10000,  # Add buffer
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': self.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            return {
                "success": True,
                "transaction_hash": receipt.transactionHash.hex(),
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "document_hash": doc_hash,
                "blockchain_verified": True
            }
        
        except Exception as e:
            logger.error(f"Failed to add verification record: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_document_on_chain(self, document_hash: str) -> Dict[str, Any]:
        """Verify a document exists on the blockchain"""
        if not self.is_connected:
            return {"success": False, "error": "Blockchain not connected"}
        
        try:
            doc_hash_bytes = self._convert_to_bytes32(document_hash)
            
            # Call contract function
            result = self.contract.functions.verifyDocument(doc_hash_bytes).call()
            
            exists, student_id, verified_by, timestamp, record_type, is_active = result
            
            if exists:
                return {
                    "success": True,
                    "verified": True,
                    "student_id": student_id,
                    "verified_by": verified_by,
                    "verified_at": datetime.fromtimestamp(timestamp, tz=timezone.utc),
                    "record_type": record_type,
                    "is_active": is_active,
                    "blockchain_verified": True
                }
            else:
                return {
                    "success": True,
                    "verified": False,
                    "message": "Document not found on blockchain"
                }
        
        except Exception as e:
            logger.error(f"Failed to verify document on blockchain: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_student_verification_history(self, student_id: str) -> Dict[str, Any]:
        """Get all verification records for a student"""
        if not self.is_connected:
            return {"success": False, "error": "Blockchain not connected"}
        
        try:
            # Check if student exists
            is_registered = self.contract.functions.isStudentRegistered(student_id).call()
            if not is_registered:
                return {"success": False, "error": "Student not registered on blockchain"}
            
            # Get records
            records = self.contract.functions.getStudentRecords(student_id).call()
            
            verification_history = []
            for record in records:
                doc_hash, verified_by, timestamp, record_type, is_active = record
                verification_history.append({
                    "document_hash": doc_hash.hex(),
                    "verified_by": verified_by,
                    "verified_at": datetime.fromtimestamp(timestamp, tz=timezone.utc),
                    "record_type": record_type,
                    "is_active": is_active
                })
            
            return {
                "success": True,
                "student_id": student_id,
                "verification_count": len(verification_history),
                "records": verification_history
            }
        
        except Exception as e:
            logger.error(f"Failed to get student verification history: {e}")
            return {"success": False, "error": str(e)}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get blockchain connection status"""
        if not self.w3:
            return {"connected": False, "error": "Web3 not initialized"}
        
        try:
            is_connected = self.w3.is_connected()
            latest_block = self.w3.eth.block_number if is_connected else None
            
            return {
                "connected": is_connected,
                "rpc_url": self.rpc_url,
                "chain_id": self.chain_id,
                "latest_block": latest_block,
                "contract_address": self.contract_address,
                "account_address": self.account.address if self.account else None
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

# Global instance
blockchain_service = BlockchainService()