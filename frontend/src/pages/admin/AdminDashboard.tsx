import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  Users,
  FileText,
  Cpu,
  ShieldCheck,
  Activity,
  Database,
  CheckCircle2,
  AlertTriangle,
  UserCheck,
  UserX,
  Clock,
  Search,
  Filter,
  RefreshCw,
  Loader2,
  Blocks,
  Share2,
} from 'lucide-react';
import {
  adminService,
  AdminStats,
  AdminUser,
  AdminAuditLog,
} from '../../services/adminService';
import { ModelMetadata } from '../../services/predictionService';

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'models' | 'logs'>('overview');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [usersList, setUsersList] = useState<AdminUser[]>([]);
  const [modelsList, setModelsList] = useState<ModelMetadata[]>([]);
  const [auditLogs, setAuditLogs] = useState<AdminAuditLog[]>([]);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [togglingId, setTogglingId] = useState<number | null>(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);
      const [statsData, usersData, modelsData, logsData] = await Promise.all([
        adminService.getStats(),
        adminService.getUsers(),
        adminService.getModels(),
        adminService.getAuditLogs(50),
      ]);
      setStats(statsData);
      setUsersList(usersData);
      setModelsList(modelsData);
      setAuditLogs(logsData);
    } catch (err) {
      console.error('Failed to load admin dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleUser = async (targetUser: AdminUser) => {
    try {
      setTogglingId(targetUser.id);
      const updated = await adminService.toggleUserStatus(targetUser.id, !targetUser.is_active);
      setUsersList((prev) => prev.map((u) => (u.id === targetUser.id ? updated : u)));
    } catch (err) {
      alert('Failed to update user status.');
    } finally {
      setTogglingId(null);
    }
  };

  const filteredUsers = usersList.filter((u) => {
    const matchesSearch =
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'all' || u.role.toLowerCase() === roleFilter.toLowerCase();
    return matchesSearch && matchesRole;
  });

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-600 font-medium">Aggregating system diagnostics & audit trails...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Admin Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-3xl p-8 text-white shadow-xl shadow-slate-900/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="text-xs uppercase tracking-widest font-bold bg-white/20 text-white px-3 py-1 rounded-full">
            Executive Admin Console
          </span>
          <h1 className="text-3xl font-extrabold mt-3 tracking-tight">System Oversight & Governance</h1>
          <p className="mt-2 text-slate-300 max-w-2xl text-sm leading-relaxed">
            Monitor patient uploads, OCR processing pipelines, scikit-learn disease prediction models, and Hardhat blockchain hash integrity in real time.
          </p>
        </div>
        <button
          onClick={loadAllData}
          className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white text-xs font-semibold px-4 py-2.5 rounded-xl border border-white/20 transition backdrop-blur-sm"
        >
          <RefreshCw className="w-4 h-4" /> Refresh Telemetry
        </button>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-600 flex items-center justify-center mb-3">
            <Users className="w-5 h-5" />
          </div>
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Patients</p>
          <h3 className="text-2xl font-extrabold text-gray-900 mt-0.5">{stats?.total_patients ?? 0}</h3>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center mb-3">
            <UserCheck className="w-5 h-5" />
          </div>
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Doctors</p>
          <h3 className="text-2xl font-extrabold text-gray-900 mt-0.5">{stats?.total_doctors ?? 0}</h3>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center mb-3">
            <FileText className="w-5 h-5" />
          </div>
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Total Reports</p>
          <h3 className="text-2xl font-extrabold text-gray-900 mt-0.5">{stats?.total_reports ?? 0}</h3>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-3">
            <Cpu className="w-5 h-5" />
          </div>
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Predictions Run</p>
          <h3 className="text-2xl font-extrabold text-gray-900 mt-0.5">{stats?.total_predictions ?? 0}</h3>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-3">
            <Blocks className="w-5 h-5" />
          </div>
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">On-Chain Hashes</p>
          <h3 className="text-2xl font-extrabold text-gray-900 mt-0.5">{stats?.total_blockchain_records ?? 0}</h3>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center mb-3">
            <Share2 className="w-5 h-5" />
          </div>
          <p className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">Active Shares</p>
          <h3 className="text-2xl font-extrabold text-gray-900 mt-0.5">{stats?.total_active_shares ?? 0}</h3>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
        {[
          { key: 'overview', label: 'ML Models & Registry', icon: Cpu },
          { key: 'users', label: 'User Directory & Access', icon: Users },
          { key: 'logs', label: 'Immutable Audit Logs', icon: Clock },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
                isActive
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content 1: Overview & ML Models */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <h3 className="font-bold text-gray-900">Registered Machine Learning Models</h3>
                <p className="text-xs text-gray-500">
                  Real evaluation metrics, validation curves, and biological input specifications.
                </p>
              </div>
              <span className="text-xs font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full">
                {modelsList.length} Active Pipelines
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {modelsList.map((m) => (
                <div key={m.disease_name} className="border border-gray-200 rounded-xl p-5 space-y-4 bg-gray-50/50">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-base text-gray-900">{m.display_name}</h4>
                      <p className="text-xs text-gray-500 mt-0.5">Algorithm: {m.algorithm} (v{m.model_version})</p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                      Trained & Serialized
                    </span>
                  </div>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-4 gap-2 pt-2 text-center">
                    <div className="bg-white p-2 rounded-lg border border-gray-200">
                      <span className="text-[10px] uppercase font-bold text-gray-400">Accuracy</span>
                      <p className="text-sm font-extrabold text-teal-700 mt-0.5">
                        {(m.evaluation_metrics.accuracy * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-gray-200">
                      <span className="text-[10px] uppercase font-bold text-gray-400">Recall</span>
                      <p className="text-sm font-extrabold text-teal-700 mt-0.5">
                        {(m.evaluation_metrics.recall * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-gray-200">
                      <span className="text-[10px] uppercase font-bold text-gray-400">F1-Score</span>
                      <p className="text-sm font-extrabold text-teal-700 mt-0.5">
                        {m.evaluation_metrics.f1_score.toFixed(3)}
                      </p>
                    </div>
                    <div className="bg-white p-2 rounded-lg border border-gray-200">
                      <span className="text-[10px] uppercase font-bold text-gray-400">ROC-AUC</span>
                      <p className="text-sm font-extrabold text-teal-700 mt-0.5">
                        {m.evaluation_metrics.roc_auc.toFixed(3)}
                      </p>
                    </div>
                  </div>

                  <div className="text-xs text-gray-600 space-y-1 pt-1">
                    <div><span className="font-semibold text-gray-700">Source:</span> {m.dataset_source}</div>
                    <div><span className="font-semibold text-gray-700">Features:</span> {m.required_features.join(', ')}</div>
                    {m.limitations && (
                      <div className="text-[11px] text-amber-800 bg-amber-50 p-2 rounded border border-amber-200 mt-2">
                        <span className="font-bold">Clinical Caveat:</span> {m.limitations}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab Content 2: Users */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm overflow-hidden space-y-4 p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-4">
            <div>
              <h3 className="font-bold text-gray-900">User Management</h3>
              <p className="text-xs text-gray-500">Manage account activation and access boundaries.</p>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search user by name or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-3 py-1.5 border border-gray-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-teal-500 w-56"
                />
              </div>

              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs outline-none"
              >
                <option value="all">All Roles</option>
                <option value="patient">Patients</option>
                <option value="doctor">Doctors</option>
                <option value="admin">Admins</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                <tr>
                  <th className="px-6 py-3">Full Name / Email</th>
                  <th className="px-6 py-3">Assigned Role</th>
                  <th className="px-6 py-3">Account Status</th>
                  <th className="px-6 py-3">Registered At</th>
                  <th className="px-6 py-3 text-right">Access Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50/50">
                    <td className="px-6 py-3.5">
                      <div className="font-semibold text-gray-900">{u.full_name}</div>
                      <div className="text-xs text-gray-500">{u.email}</div>
                    </td>
                    <td className="px-6 py-3.5">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize bg-gray-100 text-gray-700">
                        {u.role}
                      </span>
                    </td>
                    <td className="px-6 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {u.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-xs text-gray-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      {u.role !== 'admin' && (
                        <button
                          onClick={() => handleToggleUser(u)}
                          disabled={togglingId === u.id}
                          className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                            u.is_active
                              ? 'bg-rose-50 hover:bg-rose-100 text-rose-700'
                              : 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {togglingId === u.id
                            ? 'Updating...'
                            : u.is_active
                            ? 'Disable Account'
                            : 'Enable Account'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab Content 3: Audit Logs */}
      {activeTab === 'logs' && (
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-sm overflow-hidden p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div>
              <h3 className="font-bold text-gray-900">Security & Operational Audit Trail</h3>
              <p className="text-xs text-gray-500">
                Immutable event stream tracking report uploads, OCR adjustments, predictions, and blockchain events.
              </p>
            </div>
            <span className="text-xs font-semibold text-gray-400 font-mono">
              Displaying recent {auditLogs.length} events
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm font-mono text-xs">
              <thead className="bg-gray-50 text-gray-600 uppercase font-semibold">
                <tr>
                  <th className="px-6 py-3">Action</th>
                  <th className="px-6 py-3">Initiator</th>
                  <th className="px-6 py-3">Resource Target</th>
                  <th className="px-6 py-3">Details</th>
                  <th className="px-6 py-3 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50/50">
                    <td className="px-6 py-3 font-semibold text-teal-800 font-sans">
                      <span className="px-2 py-0.5 rounded bg-teal-50 border border-teal-200 text-xs">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-gray-700 font-sans">{log.user_email || `User #${log.user_id}`}</td>
                    <td className="px-6 py-3 text-gray-500 font-sans">
                      {log.resource_type} {log.resource_id ? `(${log.resource_id})` : ''}
                    </td>
                    <td className="px-6 py-3 text-gray-500 max-w-xs truncate">
                      {log.details ? JSON.stringify(log.details) : '-'}
                    </td>
                    <td className="px-6 py-3 text-right text-gray-400 font-sans text-[11px]">
                      {new Date(log.logged_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
