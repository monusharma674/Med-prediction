import React from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Cpu,
  ShieldCheck,
  Share2,
  ArrowRight,
  HeartPulse,
  Lock,
  Search,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Navigation */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-sky-600 flex items-center justify-center text-white shadow-md shadow-sky-600/30">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-lg text-slate-900">MedAI Shield</span>
              <span className="ml-2 text-xs font-medium text-sky-600 bg-sky-50 px-2 py-0.5 rounded-full border border-sky-100">
                B.Tech Major Project
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Link
              to="/login"
              className="text-sm font-semibold text-slate-700 hover:text-sky-600 px-4 py-2 transition"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="text-sm font-semibold text-white bg-sky-600 hover:bg-sky-700 px-4 py-2 rounded-lg shadow-sm transition"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 md:py-24 px-6 max-w-7xl mx-auto text-center">
        <div className="inline-flex items-center space-x-2 bg-sky-50 border border-sky-200 text-sky-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
          <Lock className="w-3.5 h-3.5" />
          <span>Intelligent Medical Report OCR + ML Risk Analysis + Blockchain Integrity</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
          AI-Powered Medical Report Management & Multi-Disease Risk Prediction
        </h1>
        <p className="mt-6 text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Upload medical lab reports in PDF or image format, automatically parse clinical parameters with OCR, evaluate eligibility for disease prediction models, and verify cryptographic report integrity with blockchain.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link
            to="/register"
            className="flex items-center space-x-2 text-base font-semibold text-white bg-sky-600 hover:bg-sky-700 px-6 py-3 rounded-xl shadow-lg shadow-sky-600/25 transition"
          >
            <span>Register as Patient or Doctor</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/login"
            className="text-base font-semibold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 px-6 py-3 rounded-xl shadow-sm transition"
          >
            Access Existing Account
          </Link>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-12 bg-white border-y border-slate-200 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center mb-4">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Automated OCR Extraction</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Dual-mode PDF parsing: native PyMuPDF extraction for digital PDFs, and Tesseract OCR for scanned lab records.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4">
              <Cpu className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Multi-Disease Risk ML</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Separate trained models for Diabetes and Heart Disease with strict schema verification and data provenance tracking.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Blockchain Tamper Verification</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              SHA-256 report hashing anchored on Solidity smart contract to prove file authenticity without storing any PII on-chain.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center mb-4">
              <Share2 className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-slate-900 text-lg mb-2">Consent-Based Sharing</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Patients selectively share reports with verified doctors, configure access expiration, or revoke permissions instantly.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8 px-6 text-center text-sm">
        <p className="font-medium text-slate-300">MedAI Shield — B.Tech Computer Engineering (AI & ML) Major Project</p>
        <p className="text-xs text-slate-500 mt-2">
          Designed and built for academic evaluation, project presentation, and viva demonstration.
        </p>
      </footer>
    </div>
  );
};
