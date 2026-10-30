import React from 'react';
import { Link, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Activity,
  FileText,
  Upload,
  Cpu,
  ShieldCheck,
  Share2,
  User as UserIcon,
  LogOut,
  Users,
  Settings,
  HeartPulse,
  Menu,
  X,
  Stethoscope,
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const { user, role, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const patientNav = [
    { name: 'Dashboard', path: '/patient/dashboard', icon: Activity },
    { name: 'Upload Report', path: '/patient/upload', icon: Upload },
    { name: 'My Reports', path: '/patient/reports', icon: FileText },
    { name: 'Disease Prediction', path: '/patient/predict', icon: Cpu },
    { name: 'Prediction History', path: '/patient/history', icon: HeartPulse },
    { name: 'Doctor Sharing', path: '/patient/sharing', icon: Share2 },
    { name: 'Blockchain Verification', path: '/patient/blockchain', icon: ShieldCheck },
    { name: 'My Profile', path: '/patient/profile', icon: UserIcon },
  ];

  const doctorNav = [
    { name: 'Doctor Dashboard', path: '/doctor/dashboard', icon: Activity },
    { name: 'Shared Patient Reports', path: '/doctor/shared-reports', icon: FileText },
    { name: 'Doctor Profile', path: '/doctor/profile', icon: Stethoscope },
  ];

  const adminNav = [
    { name: 'Admin Dashboard', path: '/admin/dashboard', icon: Activity },
    { name: 'User Management', path: '/admin/users', icon: Users },
    { name: 'ML Models & Registry', path: '/admin/models', icon: Cpu },
    { name: 'Audit & System Logs', path: '/admin/logs', icon: Settings },
  ];

  let navItems = patientNav;
  if (role === 'doctor') navItems = doctorNav;
  if (role === 'admin') navItems = adminNav;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <div className="md:hidden bg-white border-b border-slate-200 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <HeartPulse className="w-6 h-6 text-sky-600" />
          <span className="font-bold text-slate-800">MedAI Shield</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="text-slate-600 p-1 rounded-md hover:bg-slate-100"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`${
          mobileMenuOpen ? 'block' : 'hidden'
        } md:block w-full md:w-64 bg-slate-900 text-white flex-shrink-0 flex flex-col justify-between`}
      >
        <div>
          {/* Logo & Brand */}
          <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center shadow-lg shadow-sky-500/30">
              <HeartPulse className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-tight">MedAI Shield</h1>
              <p className="text-xs text-sky-400 font-medium">B.Tech Major Project</p>
            </div>
          </div>

          {/* User Role Tag */}
          <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/60">
            <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Logged in as</p>
            <div className="flex items-center justify-between mt-1">
              <span className="text-sm font-semibold text-slate-200 capitalize">{role}</span>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                  role === 'admin'
                    ? 'bg-purple-900 text-purple-200'
                    : role === 'doctor'
                    ? 'bg-emerald-900 text-emerald-200'
                    : 'bg-sky-900 text-sky-200'
                }`}
              >
                {role}
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-sky-600 text-white shadow-sm shadow-sky-600/50'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer / Logout */}
        <div className="p-4 border-t border-slate-800">
          <div className="mb-3 px-3">
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium text-rose-300 hover:bg-rose-950/40 transition-colors"
          >
            <LogOut className="w-5 h-5 text-rose-400" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top Disclaimer Banner */}
        <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center justify-between text-xs text-amber-800">
          <div className="flex items-center space-x-2">
            <span className="font-semibold uppercase tracking-wider text-[10px] bg-amber-200 text-amber-900 px-1.5 py-0.5 rounded">
              Demonstration Notice
            </span>
            <span>
              This system is developed for academic & research demonstration. It does not replace professional medical advice.
            </span>
          </div>
        </div>

        {/* Page Inner Container */}
        <div className="flex-1 p-6 md:p-8 overflow-y-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
