const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying StudentRecords contract...");

  // Get the ContractFactory and Signers here
  const StudentRecords = await ethers.getContractFactory("StudentRecords");
  
  // Deploy the contract
  const studentRecords = await StudentRecords.deploy();
  
  // Wait for deployment to finish
  await studentRecords.waitForDeployment();
  
  const contractAddress = await studentRecords.getAddress();
  
  console.log("StudentRecords contract deployed to:", contractAddress);
  console.log("Network:", await ethers.provider.getNetwork());
  
  // Get some accounts for testing
  const [deployer, ...accounts] = await ethers.getSigners();
  console.log("Deployed by account:", deployer.address);
  console.log("Account balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)));
  
  // Test the contract by registering a test student
  console.log("\nTesting contract deployment...");
  try {
    const testStudentId = "test_student_123";
    const testOwner = accounts[0].address;
    
    const registerTx = await studentRecords.registerStudent(testStudentId, testOwner);
    await registerTx.wait();
    
    const isRegistered = await studentRecords.isStudentRegistered(testStudentId);
    console.log("Test student registered successfully:", isRegistered);
    
    // Add a test verification record
    const testDocumentHash = ethers.keccak256(ethers.toUtf8Bytes("Test document content"));
    const addRecordTx = await studentRecords.addVerificationRecord(
      testStudentId, 
      testDocumentHash, 
      "transcript"
    );
    await addRecordTx.wait();
    
    console.log("Test verification record added successfully");
    console.log("Test document hash:", testDocumentHash);
    
  } catch (error) {
    console.error("Error testing contract:", error.message);
  }
  
  // Save deployment info
  const deploymentInfo = {
    contractAddress: contractAddress,
    network: "localhost",
    chainId: 31337,
    deployedBy: deployer.address,
    deployedAt: new Date().toISOString(),
    testDocumentHash: ethers.keccak256(ethers.toUtf8Bytes("Test document content"))
  };
  
  console.log("\n=== DEPLOYMENT INFO ===");
  console.log(JSON.stringify(deploymentInfo, null, 2));
  console.log("========================");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });