'use client';

import React, { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import { missingChildrenApi, sosApi, incidentsApi } from '@/lib/api';
import { MapPin, Layers, Eye, AlertTriangle, Radio, Filter } from 'lucide-react';

// Since Mapbox requires an API key, we'll create a visual placeholder map component
function MapPlaceholder() {
  const incidents = [
    { id: 1, label: 'SOS #C9102', x: 35, y: 30, type: 'sos', color: '#ef4444' },
    { id: 2, label: 'Missing MC-001', x: 55, y: 25, type: 'missing', color: '#f59e0b' },
    { id: 3, label: 'Incident CASE-001', x: 40, y: 55, type: 'incident', color: '#8b5cf6' },
    { id: 4, label: 'Missing MC-002', x: 70, y: 65, type: 'missing', color: '#f59e0b' },
    { id: 5, label: 'CCTV Candidate', x: 58, y: 28, type: 'cctv', color: '#06b6d4' },
    { id: 6, label: 'CCTV Candidate', x: 72, y: 62, type: 'cctv', color: '#06b6d4' },
    { id: 7, label: 'Incident CASE-004', x: 25, y: 70, type: 'incident', color: '#8b5cf6' },
    { id: 8, label: 'SOS #C5589', x: 80, y: 40, type: 'sos', color: '#ef4444' },
  ];

  const [hoveredPin, setHoveredPin] = useState<number | null>(null);

  return (
    <div className="relative w-full h-full bg-gradient-to-br from-[#0d1520] to-[#0f1a2e] rounded-xl overflow-hidden">
      {/* Grid overlay (fake map grid) */}
      <div className="absolute inset-0" style={{
        backgroundImage: `
          linear-gradient(rgba(6,182,212,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(6,182,212,0.03) 1px, transparent 1px)
        `,
        backgroundSize: '60px 60px'
      }} />

      {/* Fake country outline */}
      <div className="absolute inset-0 flex items-center justify-center opacity-10">
        <svg viewBox="0 0 200 250" className="w-[60%] h-[60%]" fill="none" stroke="rgba(6,182,212,0.3)" strokeWidth="0.5">
          <path d="M100,10 L130,30 L140,60 L150,80 L160,100 L155,130 L140,160 L120,180 L110,200 L100,220 L90,230 L80,220 L70,200 L60,180 L55,150 L50,120 L55,90 L60,70 L70,50 L80,30 Z" />
        </svg>
      </div>

      {/* Heat zones */}
      <div className="absolute w-40 h-40 rounded-full opacity-10" style={{ top: '15%', left: '30%', background: 'radial-gradient(circle, #ef4444, transparent)' }} />
      <div className="absolute w-32 h-32 rounded-full opacity-10" style={{ top: '55%', left: '60%', background: 'radial-gradient(circle, #f59e0b, transparent)' }} />

      {/* Map pins */}
      {incidents.map((pin) => (
        <div
          key={pin.id}
          className="absolute group cursor-pointer transition-transform hover:scale-125 z-10"
          style={{ left: `${pin.x}%`, top: `${pin.y}%`, transform: 'translate(-50%, -50%)' }}
          onMouseEnter={() => setHoveredPin(pin.id)}
          onMouseLeave={() => setHoveredPin(null)}
        >
          {/* Pulse ring */}
          <div
            className="absolute inset-0 w-8 h-8 rounded-full animate-ping opacity-20 -translate-x-1 -translate-y-1"
            style={{ background: pin.color }}
          />
          {/* Pin */}
          <div
            className="w-6 h-6 rounded-full flex items-center justify-center shadow-lg"
            style={{ background: pin.color, boxShadow: `0 0 12px ${pin.color}50` }}
          >
            {pin.type === 'sos' && <AlertTriangle size={10} className="text-white" />}
            {pin.type === 'missing' && <Eye size={10} className="text-white" />}
            {pin.type === 'incident' && <Radio size={10} className="text-white" />}
            {pin.type === 'cctv' && <MapPin size={10} className="text-white" />}
          </div>

          {/* Tooltip */}
          {hoveredPin === pin.id && (
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 rounded-lg glass-strong whitespace-nowrap animate-fade-in-scale z-20">
              <p className="text-[11px] font-semibold text-white">{pin.label}</p>
              <p className="text-[9px] text-slate-400 capitalize">{pin.type}</p>
            </div>
          )}
        </div>
      ))}

      {/* Map attribution */}
      <div className="absolute bottom-3 right-3 px-2 py-1 rounded bg-black/50 text-[9px] text-slate-500">
        Geographic Intelligence View · Connect Mapbox API for live data
      </div>
    </div>
  );
}

export default function GeoIntelPage() {
  const [activeLayer, setActiveLayer] = useState<string[]>(['sos', 'missing', 'incident', 'cctv']);
  const [sosCount, setSosCount] = useState(0);
  const [missingCount, setMissingCount] = useState(0);
  const [incidentCount, setIncidentCount] = useState(0);

  useEffect(() => {
    sosApi.getActive(50).then((data) => { if (data) setSosCount(data.length); }).catch(() => {});
    missingChildrenApi.listAlerts({ limit: 50 }).then((data) => { if (data) setMissingCount(data.length); }).catch(() => {});
    incidentsApi.getActive(50).then((data) => { if (data) setIncidentCount(data.length); }).catch(() => {});
  }, []);

  const toggleLayer = (layer: string) => {
    setActiveLayer(prev =>
      prev.includes(layer) ? prev.filter(l => l !== layer) : [...prev, layer]
    );
  };

  const layers = [
    { id: 'sos', label: 'SOS Alerts', color: '#ef4444', count: sosCount },
    { id: 'missing', label: 'Missing Children', color: '#f59e0b', count: missingCount },
    { id: 'incident', label: 'Incidents', color: '#8b5cf6', count: incidentCount },
    { id: 'cctv', label: 'CCTV Candidates', color: '#06b6d4', count: 0 },
  ];

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="Geographic Intelligence" subtitle="Spatial analysis of incidents, SOS alerts, and CCTV coverage" />

      <div className="p-3 sm:p-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
          {/* Map */}
          <div className="lg:col-span-4 glass-card overflow-hidden h-[360px] sm:h-[480px] lg:h-[calc(100vh-160px)]">
            <MapPlaceholder />
          </div>

          {/* Controls */}
          <div className="space-y-4">
            {/* Layer toggles */}
            <div className="glass-card p-5">
              <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
                <Layers size={14} className="text-cyan-400" />
                Map Layers
              </h3>
              <div className="space-y-2">
                {layers.map((layer) => (
                  <button
                    key={layer.id}
                    onClick={() => toggleLayer(layer.id)}
                    className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all text-left ${
                      activeLayer.includes(layer.id)
                        ? 'bg-white/[0.04] border border-white/[0.08]'
                        : 'opacity-50 hover:opacity-75 border border-transparent'
                    }`}
                  >
                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: layer.color }} />
                    <div className="flex-1">
                      <p className="text-xs font-medium text-slate-200">{layer.label}</p>
                    </div>
                    <span className="text-[10px] font-bold" style={{ color: layer.color }}>{layer.count}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick stats */}
            <div className="glass-card p-5">
              <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
                <MapPin size={14} className="text-emerald-400" />
                Coverage
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">Active Regions</span>
                  <span className="text-xs font-semibold text-white">{sosCount + missingCount > 0 ? 3 : 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">CCTV Feeds</span>
                  <span className="text-xs font-semibold text-white">—</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">Active SOS</span>
                  <span className="text-xs font-semibold text-red-400">{sosCount}</span>
                </div>
              </div>
            </div>

            <div className="glass-card p-4">
              <p className="text-[10px] text-slate-500">
                💡 Connect Mapbox GL JS API for live geographic data, real-time CCTV feeds, and proximity search capabilities.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
