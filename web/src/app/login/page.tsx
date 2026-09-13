'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { healthApi } from '@/lib/api';
import { Shield, UserCircle, Building, ArrowRight, Lock, Fingerprint, Server, AlertCircle, Key } from 'lucide-react';
import { UserRole } from '@/types';

export default function LoginPage() {
  const router = useRouter();
  const { loginWithCredentials, loginAsRole, isLoading, error, setError } = useAuthStore();
  const [selectedRole, setSelectedRole] = useState<UserRole | null>('moderator');
  const [email, setEmail] = useState('moderator@safety.gov.in');
  const [password, setPassword] = useState('Moderator@123');
  const [useCustomInput, setUseCustomInput] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    healthApi.check()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role);
    setError(null);
    if (role === 'moderator') {
      setEmail('moderator@safety.gov.in');
      setPassword('Moderator@123');
    } else if (role === 'admin' || role === 'authority') {
      setEmail('admin@safety.gov.in');
      setPassword('Admin@123');
    }
  };

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    let success = false;
    if (useCustomInput) {
      success = await loginWithCredentials(email, password);
    } else if (selectedRole) {
      success = await loginAsRole(selectedRole);
    }

    if (success) {
      const state = useAuthStore.getState();
      if (state.user?.role === 'authority' || state.user?.role === 'admin' || selectedRole === 'authority' || selectedRole === 'admin') {
        router.push('/authority/dashboard');
      } else {
        router.push('/moderator/dashboard');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 sm:p-6 bg-slate-950 text-slate-100">
      <div className="w-full max-w-md animate-fade-in">
        {/* Official Header Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-3 bg-blue-600 shadow-lg shadow-blue-500/20 text-white">
            <Shield size={28} />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Child Safety Portal</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">Official Child Protection & Case Intelligence Platform</p>
          
          {/* Backend Status Indicator */}
          <div className="inline-flex items-center gap-2 mt-3 px-3 py-1 rounded-full bg-slate-900 border border-slate-800">
            <Server size={12} className={backendOnline ? 'text-emerald-400' : backendOnline === false ? 'text-amber-400' : 'text-slate-400'} />
            <span className="text-[11px] text-slate-300 font-medium">
              API Connection: {backendOnline === true ? (
                <span className="text-emerald-400 font-semibold">Live Server Online</span>
              ) : backendOnline === false ? (
                <span className="text-amber-400">Offline (Demo Mode)</span>
              ) : (
                <span className="text-slate-400">Checking...</span>
              )}
            </span>
          </div>
        </div>

        {/* Card Container */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white">Institutional Sign In</h2>
              <p className="text-xs text-slate-400">Select portal or enter credentials</p>
            </div>
            <button
              onClick={() => setUseCustomInput(!useCustomInput)}
              className="text-xs text-blue-400 hover:underline flex items-center gap-1 font-medium"
            >
              <Key size={12} />
              {useCustomInput ? 'Presets' : 'Custom'}
            </button>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle size={16} className="flex-shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {!useCustomInput ? (
            /* Role Selection Presets */
            <div className="space-y-3 mb-6">
              <button
                type="button"
                onClick={() => handleRoleSelect('moderator')}
                className={`w-full flex items-center gap-3.5 p-3.5 sm:p-4 rounded-2xl border transition-all text-left ${
                  selectedRole === 'moderator'
                    ? 'border-blue-500 bg-blue-500/15 shadow-md shadow-blue-500/10'
                    : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                }`}
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  selectedRole === 'moderator' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'
                }`}>
                  <UserCircle size={22} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${selectedRole === 'moderator' ? 'text-blue-400' : 'text-slate-200'}`}>
                    Moderator Portal
                  </p>
                  <p className="text-[11px] text-slate-400 truncate">moderator@safety.gov.in</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleRoleSelect('authority')}
                className={`w-full flex items-center gap-3.5 p-3.5 sm:p-4 rounded-2xl border transition-all text-left ${
                  selectedRole === 'authority'
                    ? 'border-amber-500 bg-amber-500/15 shadow-md shadow-amber-500/10'
                    : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                }`}
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  selectedRole === 'authority' ? 'bg-amber-600 text-white' : 'bg-slate-800 text-slate-400'
                }`}>
                  <Building size={22} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${selectedRole === 'authority' ? 'text-amber-400' : 'text-slate-200'}`}>
                    Authority & Law Enforcement
                  </p>
                  <p className="text-[11px] text-slate-400 truncate">admin@safety.gov.in</p>
                </div>
              </button>
            </div>
          ) : (
            /* Custom Email & Password Inputs */
            <form onSubmit={handleLogin} className="space-y-4 mb-6">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="moderator@safety.gov.in"
                  className="input-field text-xs sm:text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field text-xs sm:text-sm"
                  required
                />
              </div>
            </form>
          )}

          {/* Seeded Credentials info */}
          <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-950 border border-slate-800 mb-6">
            <Fingerprint size={14} className="text-blue-400 flex-shrink-0" />
            <p className="text-[11px] text-slate-300">
              Seeded Auth: <span className="font-semibold text-white">moderator@safety.gov.in</span> / <span className="font-semibold text-white">Moderator@123</span>
            </p>
          </div>

          {/* Login Button */}
          <button
            onClick={() => handleLogin()}
            disabled={isLoading}
            className="btn-primary w-full justify-center !py-3 !text-sm cursor-pointer shadow-lg shadow-blue-500/20"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                Sign In to Platform
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-[11px] text-slate-500">
            Protected by JWT Bearer Auth · Statutory Compliance (POCSO & DPDP Act 2023)
          </p>
        </div>
      </div>
    </div>
  );
}
