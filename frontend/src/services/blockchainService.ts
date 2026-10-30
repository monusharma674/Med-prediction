import api from './api';

export interface BlockchainRecord {
  report_id: number;
  report_uuid: string;
  file_hash_sha256: string;
  tx_hash: string;
  contract_address: string;
  network_name: string;
  block_number: number;
  registered_at: string;
}

export interface BlockchainVerifyResult {
  report_id: number;
  report_uuid: string;
  current_disk_hash: string;
  blockchain_anchored_hash?: string | null;
  is_verified: boolean;
  is_registered_on_chain: boolean;
  tx_hash?: string | null;
  block_number?: number | null;
  registered_at?: string | null;
  integrity_status: string;
}

export const blockchainService = {
  async registerReport(reportId: number): Promise<BlockchainRecord> {
    const res = await api.post(`/blockchain/register/${reportId}`);
    return res.data;
  },

  async verifyReport(reportId: number): Promise<BlockchainVerifyResult> {
    const res = await api.get(`/blockchain/verify/${reportId}`);
    return res.data;
  },

  async getAuditTrail(limit: number = 20): Promise<BlockchainRecord[]> {
    const res = await api.get('/blockchain/audit-trail', { params: { limit } });
    return res.data;
  },
};
