const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log("Starting local Hardhat blockchain node...");

// Start Hardhat node
const hardhatNode = spawn('npx', ['hardhat', 'node'], {
  stdio: 'pipe',
  detached: false
});

let nodeStarted = false;
let contractDeployed = false;

hardhatNode.stdout.on('data', (data) => {
  const output = data.toString();
  console.log(output);
  
  // Check if node is ready
  if (output.includes('Started HTTP and WebSocket JSON-RPC server') && !nodeStarted) {
    nodeStarted = true;
    console.log('\n🚀 Blockchain node is ready!');
    
    // Deploy contract after a short delay
    setTimeout(deployContract, 2000);
  }
});

hardhatNode.stderr.on('data', (data) => {
  console.error('Node error:', data.toString());
});

hardhatNode.on('close', (code) => {
  console.log(`Hardhat node process exited with code ${code}`);
});

async function deployContract() {
  if (contractDeployed) return;
  contractDeployed = true;
  
  console.log('\n📋 Deploying StudentRecords contract...');
  
  const deployScript = spawn('npx', ['hardhat', 'run', 'scripts/deploy.js', '--network', 'localhost'], {
    stdio: 'pipe'
  });
  
  let deploymentInfo = '';
  
  deployScript.stdout.on('data', (data) => {
    const output = data.toString();
    console.log(output);
    deploymentInfo += output;
  });
  
  deployScript.stderr.on('data', (data) => {
    console.error('Deploy error:', data.toString());
  });
  
  deployScript.on('close', (code) => {
    if (code === 0) {
      console.log('\n✅ Contract deployed successfully!');
      
      // Extract contract address and save to env
      const addressMatch = deploymentInfo.match(/StudentRecords contract deployed to: (0x[a-fA-F0-9]{40})/);
      if (addressMatch) {
        const contractAddress = addressMatch[1];
        updateEnvFile(contractAddress);
        console.log(`\n🔗 Contract address: ${contractAddress}`);
        console.log('📝 Updated backend/.env with contract address');
      }
    } else {
      console.error('❌ Contract deployment failed');
    }
  });
}

function updateEnvFile(contractAddress) {
  const envPath = path.join(__dirname, '..', 'backend', '.env');
  let envContent = '';
  
  try {
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }
    
    // Update or add blockchain configuration
    const updates = {
      'BLOCKCHAIN_RPC_URL': 'http://localhost:8545',
      'BLOCKCHAIN_CONTRACT_ADDRESS': contractAddress,
      'BLOCKCHAIN_CHAIN_ID': '31337',
      'BLOCKCHAIN_PRIVATE_KEY': '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
    };
    
    Object.entries(updates).forEach(([key, value]) => {
      const regex = new RegExp(`^${key}=.*$`, 'm');
      if (envContent.match(regex)) {
        envContent = envContent.replace(regex, `${key}="${value}"`);
      } else {
        envContent += `\n${key}="${value}"`;
      }
    });
    
    fs.writeFileSync(envPath, envContent);
    console.log('✅ Environment file updated successfully');
    
  } catch (error) {
    console.error('❌ Error updating environment file:', error);
  }
}

// Handle process termination
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down blockchain node...');
  hardhatNode.kill();
  process.exit();
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Shutting down blockchain node...');
  hardhatNode.kill();
  process.exit();
});