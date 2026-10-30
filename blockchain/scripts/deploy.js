const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("Deploying MedicalReportRegistry smart contract to local network...");

  const MedicalReportRegistry = await hre.ethers.getContractFactory("MedicalReportRegistry");
  const registry = await MedicalReportRegistry.deploy();
  await registry.waitForDeployment();

  const contractAddress = await registry.getAddress();
  console.log(`MedicalReportRegistry deployed successfully at: ${contractAddress}`);

  // Export contract deployment address and ABI for backend and frontend integration
  const deploymentInfo = {
    network: hre.network.name,
    chainId: hre.network.config.chainId || 1337,
    contractAddress: contractAddress,
    deployedAt: new Date().toISOString(),
  };

  const outputDir = path.join(__dirname, "..", "deployed");
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const outputPath = path.join(outputDir, "contract_address.json");
  fs.writeFileSync(outputPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`Deployment info saved to: ${outputPath}`);

  // Copy to backend config if accessible
  const backendConfigPath = path.join(__dirname, "..", "..", "backend", "app", "core", "blockchain_deployment.json");
  fs.writeFileSync(backendConfigPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`Deployment info synchronized with backend at: ${backendConfigPath}`);
}

main().catch((error) => {
  console.error("Deployment failed:", error);
  process.exitCode = 1;
});
