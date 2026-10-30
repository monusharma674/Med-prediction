import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  ShieldCheck,
  ShieldAlert,
  Blocks,
  Hash,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Copy,
  ExternalLink,
  Lock,
  FileText,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import {
  blockchainService,
  BlockchainRecord,
  BlockchainVerifyResult,
} from '../../services/blockchainService';
import { reportService, MedicalReportSummary } from '../../services/reportService';

export const BlockchainVerificationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const urlReportId = searchParams.get('report_id');

  const [reports, setReports] = useState<MedicalReportSummary[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(
    urlReportId ? parseInt(urlReportId, 10) : null
  );
  const [verifying, setVerifying] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [verifyResult, setVerifyResult] = useState<BlockchainVerifyResult | null>(null);
  const [auditTrail, setAuditTrail] = useState<BlockchainRecord[]>([]);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
    loadAuditTrail();
  }, []);

  useEffect(() => {
    if (selectedReportId) {
      handleVerify(selectedReportId);
    }
  }, [selectedReportId]);

  const loadReports = async () => {
    try {
      const data = await reportService.getMyReports();
      setReports(data);
      if (!selectedReportId && data.length > 0) {
        setSelectedReportId(data[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load patient reports:', err);
    }
  };

  const loadAuditTrail = async () => {
    try {
      const trail = await blockchainService.getAuditTrail(15);
      setAuditTrail(trail);
    } catch (err: any) {
      console.error('Failed to load audit trail:', err);
    }
  };

  const handleVerify = async (reportId: number) => {
    try {
      setVerifying(true);
      setErrorMessage(null);
      const res = await blockchainService.verifyReport(reportId);
      setVerifyResult(res);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Verification request failed.');
    } finally {
      setVerifying(false);
    }
  };

  const handleRegisterOnChain = async () => {
    if (!selectedReportId) return;
    try {
      setRegistering(true);
      setErrorMessage(null);
      await blockchainService.registerReport(selectedReportId);
      await handleVerify(selectedReportId);
      await loadAuditTrail();
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to anchor report hash on blockchain.');
    } finally {
      setRegistering(false);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const selectedReport = reports.find((r) => r.id === selectedReportId);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider font-bold text-teal-600 mb-1">
          <Blocks className="w-4 h-4" />
          Cryptographic Integrity & Blockchain Verification
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-gray-900 tracking-tight">
          Report Hash Anchoring & Verification Console
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Verify the mathematical immutability and authenticity of your medical records using SHA-256 digests anchored on an Ethereum-compatible distributed ledger.
        </p>
      </div>

      {/* Security Guarantee Banner */}
      <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start gap-3 text-sky-900 text-sm">
        <Lock className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Zero-Knowledge Patient Privacy:</span> Only the 32-byte cryptographic
          SHA-256 digest of your original medical document is registered on the blockchain. No personal identifiable
          information (PII), names, or raw medical test values ever touch the blockchain.
        </div>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Verification Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Report Selector Card */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
          <h2 className="text-base font-bold text-gray-900">Select Medical Report</h2>
          <p className="text-xs text-gray-500">
            Choose a report from your vault to run a real-time cryptographic audit.
          </p>

          <div className="space-y-2">
            {reports.map((r) => {
              const isSelected = r.id === selectedReportId;
              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedReportId(r.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-teal-600 bg-teal-50/50 ring-1 ring-teal-600'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-gray-900 truncate max-w-[180px]">
                      {r.original_filename}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        r.blockchain_registered
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {r.blockchain_registered ? 'Anchored' : 'Unanchored'}
                    </span>
                  </div>
                  <div className="text-[11px] text-gray-400 mt-1">
                    UUID: {r.report_uuid.slice(0, 16)}...
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Verification Status & Hash Inspector */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <div>
                <h3 className="font-bold text-gray-900">Cryptographic Verification Status</h3>
                <p className="text-xs text-gray-500">
                  Bit-for-bit comparison between server file bytes and immutable ledger.
                </p>
              </div>
              {selectedReportId && (
                <button
                  onClick={() => handleVerify(selectedReportId)}
                  disabled={verifying}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
                  Re-Verify
                </button>
              )}
            </div>

            {verifying ? (
              <div className="py-12 flex flex-col items-center justify-center">
                <Loader2 className="w-8 h-8 text-teal-600 animate-spin mb-3" />
                <p className="text-sm text-gray-500">Computing SHA-256 and querying blockchain node...</p>
              </div>
            ) : verifyResult ? (
              <div className="space-y-6">
                {/* Result Hero Banner */}
                {verifyResult.is_registered_on_chain ? (
                  verifyResult.is_verified ? (
                    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3">
                      <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-bold text-emerald-950 text-sm">
                          Bitwise Cryptographic Verification Succeeded
                        </h4>
                        <p className="text-xs text-emerald-800 mt-0.5">
                          The physical report file currently residing on the server matches the exact SHA-256 digest
                          anchored to the blockchain ledger. No unauthorized modification or data corruption has occurred.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3">
                      <ShieldAlert className="w-6 h-6 text-rose-600 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-bold text-rose-950 text-sm">
                          Tampering or Corruption Detected!
                        </h4>
                        <p className="text-xs text-rose-800 mt-0.5">
                          Warning: The SHA-256 digest of the current file does not match the blockchain hash registered on
                          ingestion. The file content has been altered!
                        </p>
                      </div>
                    </div>
                  )
                ) : (
                  <div className="p-5 bg-amber-50 border border-amber-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-bold text-amber-950 text-sm">Not Yet Anchored on Blockchain</h4>
                        <p className="text-xs text-amber-800 mt-0.5">
                          This medical report has a valid SHA-256 checksum locally, but has not yet been registered onto the blockchain registry.
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleRegisterOnChain}
                      disabled={registering}
                      className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center gap-2 self-start sm:self-auto disabled:opacity-50"
                    >
                      {registering ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          Anchoring...
                        </>
                      ) : (
                        <>
                          <Blocks className="w-3.5 h-3.5" />
                          Anchor to Blockchain
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* Hashes Comparison Table */}
                <div className="space-y-3">
                  <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                      <span className="font-semibold text-gray-700 flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5" /> Current File SHA-256 Digest (On Server Disk)
                      </span>
                      <button
                        onClick={() => copyToClipboard(verifyResult.current_disk_hash, 'disk')}
                        className="text-[11px] text-teal-600 hover:underline flex items-center gap-1"
                      >
                        {copiedKey === 'disk' ? 'Copied!' : 'Copy Hash'}
                      </button>
                    </div>
                    <div className="font-mono text-xs text-gray-800 break-all select-all">
                      {verifyResult.current_disk_hash}
                    </div>
                  </div>

                  <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                      <span className="font-semibold text-gray-700 flex items-center gap-1.5">
                        <Blocks className="w-3.5 h-3.5" /> Blockchain Anchored Hash (Immutable Ledger)
                      </span>
                      {verifyResult.blockchain_anchored_hash && (
                        <button
                          onClick={() => copyToClipboard(verifyResult.blockchain_anchored_hash!, 'chain')}
                          className="text-[11px] text-teal-600 hover:underline flex items-center gap-1"
                        >
                          {copiedKey === 'chain' ? 'Copied!' : 'Copy Hash'}
                        </button>
                      )}
                    </div>
                    <div className="font-mono text-xs text-gray-800 break-all select-all">
                      {verifyResult.blockchain_anchored_hash || 'None (Pending Anchoring)'}
                    </div>
                  </div>
                </div>

                {/* Ledger Transaction Details */}
                {verifyResult.is_registered_on_chain && (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                    <div className="p-3 bg-teal-50/40 border border-teal-100 rounded-lg">
                      <span className="text-[11px] uppercase font-semibold text-teal-700">Block Number</span>
                      <p className="text-sm font-bold text-gray-900 mt-0.5">#{verifyResult.block_number}</p>
                    </div>
                    <div className="p-3 bg-teal-50/40 border border-teal-100 rounded-lg">
                      <span className="text-[11px] uppercase font-semibold text-teal-700">Network</span>
                      <p className="text-sm font-bold text-gray-900 mt-0.5">Hardhat Local (Chain 1337)</p>
                    </div>
                    <div className="p-3 bg-teal-50/40 border border-teal-100 rounded-lg">
                      <span className="text-[11px] uppercase font-semibold text-teal-700">Timestamp</span>
                      <p className="text-xs font-semibold text-gray-900 mt-1">
                        {verifyResult.registered_at ? new Date(verifyResult.registered_at).toLocaleString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Blockchain Ledger Audit Trail */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900">Immutable Ledger Audit Trail</h3>
            <p className="text-xs text-gray-500">
              Live transaction stream from MedicalReportRegistry smart contract.
            </p>
          </div>
          <span className="text-xs text-gray-400 font-mono">
            Contract: 0x5FbDB2315678afecb367f032d93F642f64180aa3
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
              <tr>
                <th className="px-6 py-3">Block #</th>
                <th className="px-6 py-3">Report UUID</th>
                <th className="px-6 py-3">Transaction Hash</th>
                <th className="px-6 py-3">SHA-256 Digest</th>
                <th className="px-6 py-3">Anchored At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono text-xs">
              {auditTrail.map((record) => (
                <tr key={record.tx_hash} className="hover:bg-gray-50/60">
                  <td className="px-6 py-3.5 font-bold text-teal-700">#{record.block_number}</td>
                  <td className="px-6 py-3.5 text-gray-700 font-sans">{record.report_uuid}</td>
                  <td className="px-6 py-3.5 text-gray-500">
                    {record.tx_hash.slice(0, 14)}...{record.tx_hash.slice(-8)}
                  </td>
                  <td className="px-6 py-3.5 text-gray-500">
                    {record.file_hash_sha256.slice(0, 12)}...{record.file_hash_sha256.slice(-6)}
                  </td>
                  <td className="px-6 py-3.5 text-gray-400 font-sans text-[11px]">
                    {new Date(record.registered_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
