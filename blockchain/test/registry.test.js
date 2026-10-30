const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("MedicalReportRegistry", function () {
  let registry;
  let owner;
  let user1;

  beforeEach(async function () {
    [owner, user1] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("MedicalReportRegistry");
    registry = await Factory.deploy();
    await registry.waitForDeployment();
  });

  it("should deploy with the correct owner", async function () {
    expect(await registry.owner()).to.equal(owner.address);
  });

  it("should register a report SHA-256 hash successfully and emit event", async function () {
    const reportUUID = "rep-uuid-999";
    const sampleHashHex = ethers.keccak256(ethers.toUtf8Bytes("sample_pdf_report_bytes"));

    await expect(registry.registerReportHash(reportUUID, sampleHashHex))
      .to.emit(registry, "ReportHashRegistered");

    const record = await registry.getReportRecord(reportUUID);
    expect(record.exists).to.be.true;
    expect(record.fileHashSha256).to.equal(sampleHashHex);
  });

  it("should prevent duplicate registration of the same report UUID", async function () {
    const reportUUID = "rep-uuid-duplicate";
    const sampleHash = ethers.keccak256(ethers.toUtf8Bytes("content_1"));

    await registry.registerReportHash(reportUUID, sampleHash);

    await expect(
      registry.registerReportHash(reportUUID, sampleHash)
    ).to.be.revertedWith("Report hash is already registered on blockchain");
  });

  it("should correctly verify report integrity", async function () {
    const reportUUID = "rep-uuid-verify";
    const originalHash = ethers.keccak256(ethers.toUtf8Bytes("original_report"));
    const tamperedHash = ethers.keccak256(ethers.toUtf8Bytes("tampered_report"));

    await registry.registerReportHash(reportUUID, originalHash);

    // Verify with genuine hash
    const [isMatchGenuine, isFoundGenuine] = await registry.verifyReportIntegrity(reportUUID, originalHash);
    expect(isFoundGenuine).to.be.true;
    expect(isMatchGenuine).to.be.true;

    // Verify with altered/tampered hash
    const [isMatchTampered, isFoundTampered] = await registry.verifyReportIntegrity(reportUUID, tamperedHash);
    expect(isFoundTampered).to.be.true;
    expect(isMatchTampered).to.be.false;
  });
});
