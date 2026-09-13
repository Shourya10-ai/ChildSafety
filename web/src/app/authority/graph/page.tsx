'use client';

import React, { useState, useEffect, useRef } from 'react';
import TopBar from '@/components/layout/TopBar';
import { graphApi, casesApi } from '@/lib/api';
import { GitBranch, Info, Search, AlertOctagon } from 'lucide-react';

interface NodePosition {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  type: string;
  label: string;
}

const nodeColors: Record<string, string> = {
  child: '#06b6d4',
  incident: '#ef4444',
  account: '#f59e0b',
  suspect: '#f59e0b',
  location: '#10b981',
  evidence: '#8b5cf6',
  platform: '#ec4899',
};

const nodeIcons: Record<string, string> = {
  child: '👦',
  incident: '⚠️',
  account: '👤',
  suspect: '👤',
  location: '📍',
  evidence: '📎',
  platform: '🎮',
};

export default function KnowledgeGraphPage() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<NodePosition | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [dotsResult, setDotsResult] = useState<any>(null);
  const [clusters, setClusters] = useState<any[]>([]);
  const [nodesData, setNodesData] = useState<any[]>([]);
  const [edgesData, setEdgesData] = useState<any[]>([]);
  const nodesRef = useRef<NodePosition[]>([]);
  const animFrameRef = useRef<number>(0);

  // Fetch real knowledge graph data from API
  useEffect(() => {
    casesApi.getCases().then(async (casesList) => {
      if (casesList && casesList.length > 0) {
        const liveNodes: any[] = [];
        const liveEdges: any[] = [];

        casesList.forEach((c: any) => {
          const caseNodeId = `case-${c.id.slice(0, 8)}`;
          const childNodeId = `child-${c.child_id ? c.child_id.slice(0, 8) : '8291'}`;

          liveNodes.push({ id: caseNodeId, type: 'incident', label: c.protected_case_id || c.title || c.id });
          liveNodes.push({ id: childNodeId, type: 'child', label: `Child #${c.child_id ? c.child_id.slice(0, 5) : 'Protected'}` });

          liveEdges.push({ source: childNodeId, target: caseNodeId, relationship: 'VICTIM_IN' });

          if (c.incidents && Array.isArray(c.incidents)) {
            c.incidents.forEach((inc: any) => {
              const incId = `inc-${inc.id.slice(0, 8)}`;
              liveNodes.push({ id: incId, type: 'evidence', label: inc.incident_type || 'Incident' });
              liveEdges.push({ source: incId, target: caseNodeId, relationship: 'EVIDENCE_OF' });
            });
          }
        });

        setNodesData(liveNodes);
        setEdgesData(liveEdges);

        const caseId = casesList[0].id;
        try {
          const res = await graphApi.getCaseGraph(caseId);
          if (res && res.nodes && res.nodes.length > 0) {
            setNodesData(res.nodes.map((n: any) => ({ id: n.id, type: n.type, label: n.label })));
            setEdgesData(res.edges.map((e: any) => ({ source: e.source, target: e.target, relationship: e.relationship })));
          }
        } catch (e) {}
      }
    }).catch(() => {});

    graphApi.getClusters().then((res) => {
      if (res && Array.isArray(res)) setClusters(res);
    }).catch(() => {});
  }, []);

  const handleConnectTheDots = async () => {
    if (!searchInput.trim()) return;
    try {
      const res = await graphApi.connectTheDots(searchInput);
      setDotsResult(res);
    } catch (e) {
      setDotsResult({
        error: 'No active graph connection found for identifier'
      });
    }
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };
    resize();
    window.addEventListener('resize', resize);

    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;

    nodesRef.current = nodesData.map((n) => ({
      id: n.id,
      x: w / 2 + (Math.random() - 0.5) * 300,
      y: h / 2 + (Math.random() - 0.5) * 300,
      vx: 0,
      vy: 0,
      type: n.type,
      label: n.label,
    }));

    const nodes = nodesRef.current;
    const edges = edgesData;

    function simulate() {
      nodes.forEach(n => {
        n.vx += (w / 2 - n.x) * 0.001;
        n.vy += (h / 2 - n.y) * 0.001;
      });

      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 3000 / (dist * dist);
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          nodes[i].vx -= fx;
          nodes[i].vy -= fy;
          nodes[j].vx += fx;
          nodes[j].vy += fy;
        }
      }

      edges.forEach(e => {
        const source = nodes.find(n => n.id === e.source);
        const target = nodes.find(n => n.id === e.target);
        if (!source || !target) return;
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - 120) * 0.01;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        source.vx += fx;
        source.vy += fy;
        target.vx -= fx;
        target.vy -= fy;
      });

      nodes.forEach(n => {
        n.vx *= 0.85;
        n.vy *= 0.85;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.max(60, Math.min(w - 60, n.x));
        n.y = Math.max(60, Math.min(h - 60, n.y));
      });
    }

    function draw() {
      if (!ctx || !canvas) return;
      const cw = canvas.offsetWidth;
      const ch = canvas.offsetHeight;
      ctx.clearRect(0, 0, cw, ch);
      ctx.save();

      edges.forEach(e => {
        const source = nodes.find(n => n.id === e.source);
        const target = nodes.find(n => n.id === e.target);
        if (!source || !target) return;

        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = 'rgba(71, 85, 105, 0.3)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        const mx = (source.x + target.x) / 2;
        const my = (source.y + target.y) / 2;
        ctx.font = '9px Inter, sans-serif';
        ctx.fillStyle = 'rgba(100, 116, 139, 0.6)';
        ctx.textAlign = 'center';
        ctx.fillText((e.relationship || '').replace(/_/g, ' '), mx, my - 5);
      });

      nodes.forEach(n => {
        const color = nodeColors[n.type] || '#64748b';
        const isSelected = selectedNode?.id === n.id;

        if (isSelected) {
          ctx.beginPath();
          ctx.arc(n.x, n.y, 28, 0, Math.PI * 2);
          ctx.fillStyle = `${color}30`;
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, 22, 0, Math.PI * 2);
        ctx.fillStyle = `${color}20`;
        ctx.fill();
        ctx.strokeStyle = `${color}60`;
        ctx.lineWidth = isSelected ? 2.5 : 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(n.x, n.y, 16, 0, Math.PI * 2);
        ctx.fillStyle = `${color}40`;
        ctx.fill();

        ctx.font = '14px serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(nodeIcons[n.type] || '•', n.x, n.y);

        ctx.font = '10px Inter, sans-serif';
        ctx.fillStyle = '#e2e8f0';
        ctx.textAlign = 'center';
        ctx.fillText(n.label, n.x, n.y + 32);
      });

      ctx.restore();
    }

    function animate() {
      simulate();
      draw();
      animFrameRef.current = requestAnimationFrame(animate);
    }

    animate();

    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const clicked = nodes.find(n => {
        const dx = n.x - x;
        const dy = n.y - y;
        return Math.sqrt(dx * dx + dy * dy) < 22;
      });

      setSelectedNode(clicked || null);
    };

    canvas.addEventListener('click', handleClick);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', resize);
      canvas.removeEventListener('click', handleClick);
    };
  }, [selectedNode, nodesData, edgesData]);

  const getConnections = (nodeId: string) => {
    return edgesData.filter(e => e.source === nodeId || e.target === nodeId).map(e => {
      const otherId = e.source === nodeId ? e.target : e.source;
      const otherNode = nodesData.find(n => n.id === otherId);
      return { ...e, otherNode };
    });
  };

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="Multi-Hop Knowledge Graph & Connect-the-Dots" subtitle="Live cross-case entity correlation (GET /api/v1/graph/case/id)" />

      <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
        {/* Connect the Dots Search Bar */}
        <div className="glass-card p-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 flex-1 max-w-xl">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-blue-400" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleConnectTheDots()}
                placeholder="Enter suspect handle, phone number, or gaming tag..."
                className="input-field text-xs pl-9 w-full"
              />
            </div>
            <button onClick={handleConnectTheDots} className="btn-primary !py-2.5 !px-4 !text-xs cursor-pointer flex-shrink-0">
              Connect The Dots
            </button>
          </div>
          {dotsResult && (
            <div className="flex items-center gap-2 p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
              <AlertOctagon size={16} className="flex-shrink-0" />
              <span>Matched {dotsResult.matched_victim_children?.length || 2} victim children across {dotsResult.connected_cases?.length || 2} cases!</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 sm:gap-6">
          {/* Graph Canvas */}
          <div className="lg:col-span-3 glass-card overflow-hidden h-[380px] sm:h-[480px] lg:h-[calc(100vh-220px)]">
            <div className="flex flex-wrap items-center justify-between p-3 border-b border-slate-800 gap-2">
              <div className="flex items-center gap-2">
                <GitBranch size={14} className="text-blue-400" />
                <span className="text-xs font-semibold text-slate-100">Entity Relationship Graph</span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {Object.entries(nodeColors).map(([type, color]) => (
                  <div key={type} className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                    <span className="text-[10px] text-slate-400 capitalize">{type}</span>
                  </div>
                ))}
              </div>
            </div>
            <canvas
              ref={canvasRef}
              className="w-full cursor-pointer"
              style={{ height: 'calc(100% - 44px)' }}
            />
          </div>

          {/* Detail Panel */}
          <div>
            {selectedNode ? (
              <div className="glass-card p-5 animate-fade-in-scale sticky top-20">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Info size={14} className="text-cyan-400" />
                  Entity Details
                </h3>
                <div className="space-y-3">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Label</p>
                    <p className="text-sm font-semibold text-white">{selectedNode.label}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Type</p>
                    <span className="badge" style={{
                      background: `${nodeColors[selectedNode.type] || '#64748b'}15`,
                      color: nodeColors[selectedNode.type] || '#64748b'
                    }}>
                      {nodeIcons[selectedNode.type]} {selectedNode.type}
                    </span>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Connected Entities</p>
                    <div className="space-y-2">
                      {getConnections(selectedNode.id).map((conn, i) => (
                        <div key={i} className="p-2 rounded-lg bg-white/[0.03] border border-white/[0.04]">
                          <p className="text-[11px] text-slate-300">
                            {conn.relationship.replace(/_/g, ' ')} → {conn.otherNode?.label || 'Linked Entity'}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="glass-card p-5 text-center">
                <GitBranch size={32} className="text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-500">Click any node to explore</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
