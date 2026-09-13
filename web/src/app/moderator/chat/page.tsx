'use client';

import React, { useState, useRef, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import { chatApi, casesApi } from '@/lib/api';
import { realtimeService } from '@/lib/websocket';
import { timeAgo } from '@/lib/utils';
import { RiskBadge } from '@/components/shared/Badges';
import { MessageSquare, Send, Users, Paperclip, Shield } from 'lucide-react';

export default function ChatPage() {
  const [selectedChild, setSelectedChild] = useState<string>('');
  const [caseId, setCaseId] = useState<string>('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Record<string, any[]>>({});
  const [activeChatCases, setActiveChatCases] = useState<any[]>([]);
  const [showMobileList, setShowMobileList] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    realtimeService.connect();

    casesApi.getCases().then((list) => {
      if (list && list.length > 0) {
        setActiveChatCases(list);
        const first = list[0];
        setCaseId(first.id);
        setSelectedChild(first.protected_case_id || `#C${first.child_id ? first.child_id.slice(0, 4) : first.id.slice(0, 4)}`);
      }
    }).catch(() => {});
  }, []);

  const currentMessages = messages[selectedChild] || [];
  const childrenWithChats = activeChatCases.map(c => ({
    id: c.protected_case_id || `#C${c.child_id ? c.child_id.slice(0, 4) : c.id.slice(0, 4)}`,
    caseRawId: c.id,
    title: c.title || 'Child Support Case',
    activeCases: 1,
    riskLevel: (c.risk_level || c.priority || 'high').toLowerCase(),
  }));

  // Load chat history from API
  useEffect(() => {
    if (!caseId) return;

    chatApi.getMessages(caseId).then((res) => {
      const msgList = Array.isArray(res) ? res : (res?.messages || res?.items || []);
      if (Array.isArray(msgList)) {
        const formatted = msgList.map((m: any) => ({
          id: m.id,
          senderId: m.sender_id || m.senderId || 'user',
          senderRole: (m.sender_role || m.senderRole || 'child') as any,
          content: m.content,
          timestamp: m.created_at || m.timestamp || new Date().toISOString(),
          read: m.is_read ?? m.read ?? true,
        }));
        setMessages((prev) => ({ ...prev, [selectedChild]: formatted }));
      }
    }).catch(() => {});

    // Listen for real-time CHAT_MESSAGE WebSocket events (Section 5.6.1)
    const unsubscribe = realtimeService.subscribe((event, data) => {
      if (event === 'CHAT_MESSAGE' && data.message) {
        const msg = data.message;
        const newMsg = {
          id: msg.id || `MSG-${Date.now()}`,
          senderId: msg.sender_id || 'child-1',
          senderRole: (msg.sender_role || 'child') as any,
          content: msg.content,
          timestamp: msg.created_at || new Date().toISOString(),
          read: false,
        };
        setMessages((prev) => ({
          ...prev,
          [selectedChild]: [...(prev[selectedChild] || []), newMsg],
        }));
      }
    });

    return () => unsubscribe();
  }, [caseId, selectedChild]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMessages.length, selectedChild]);

  const handleSend = async () => {
    if (!message.trim()) return;
    const text = message;
    setMessage('');

    try {
      await chatApi.sendMessage(caseId, text);
    } catch (e) {
      console.warn('API send message fallback');
    }

    const newMsg = {
      id: `MSG-${Date.now()}`,
      senderId: 'M1042',
      senderRole: 'moderator' as const,
      content: text,
      timestamp: new Date().toISOString(),
      read: true,
    };
    setMessages(prev => ({
      ...prev,
      [selectedChild]: [...(prev[selectedChild] || []), newMsg],
    }));
  };

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="Communication Hub" subtitle="Live confidential messaging (POST /api/v1/chat/cases/id/messages)" />

      <div className="p-3 sm:p-6">
        <div className="glass-card overflow-hidden h-[calc(100vh-180px)] md:h-[calc(100vh-140px)]">
          <div className="flex h-full relative">
            {/* Children sidebar */}
            <div className={`w-full md:w-80 border-r border-slate-800 flex-col bg-slate-900/90 md:bg-transparent ${
              showMobileList ? 'flex absolute inset-0 z-20 md:relative md:z-auto' : 'hidden md:flex'
            }`}>
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                  <Users size={14} className="text-blue-400" />
                  Children Support Cases
                </h3>
                {showMobileList && (
                  <button
                    onClick={() => setShowMobileList(false)}
                    className="md:hidden text-xs text-blue-400 font-semibold px-2 py-1 bg-blue-500/10 rounded"
                  >
                    Done
                  </button>
                )}
              </div>
              <div className="flex-1 overflow-y-auto divide-y divide-slate-800/40">
                {childrenWithChats.map((child) => {
                  const childMsgs = messages[child.id] || [];
                  const lastMsg = childMsgs[childMsgs.length - 1];
                  const unread = childMsgs.filter(m => !m.read && m.senderRole === 'child').length;

                  return (
                    <button
                      key={child.id}
                      onClick={() => {
                        setSelectedChild(child.id);
                        setCaseId(child.id === '#C8291' ? 'CASE-001' : 'CASE-002');
                        setShowMobileList(false);
                      }}
                      className={`w-full flex items-center gap-3 p-4 text-left transition-all ${
                        selectedChild === child.id
                          ? 'bg-blue-600/15 border-l-4 border-l-blue-500'
                          : 'hover:bg-slate-800/40 border-l-4 border-l-transparent'
                      }`}
                    >
                      <div className="w-9 h-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-blue-400">{child.id.slice(1, 4)}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-slate-200">{child.id}</span>
                          {unread > 0 && (
                            <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center">
                              {unread}
                            </span>
                          )}
                        </div>
                        {lastMsg && (
                          <p className="text-[11px] text-slate-400 truncate mt-0.5">{lastMsg.content}</p>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Chat area */}
            <div className={`flex-1 flex flex-col ${showMobileList ? 'hidden md:flex' : 'flex'}`}>
              {/* Chat header */}
              <div className="flex items-center justify-between p-3.5 sm:p-4 border-b border-slate-800 bg-slate-900/40">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setShowMobileList(true)}
                    className="md:hidden p-1.5 rounded-lg bg-slate-800 text-blue-400 font-semibold text-xs flex items-center gap-1"
                  >
                    <Users size={14} /> Cases
                  </button>
                  <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                    <Shield size={14} className="text-blue-400" />
                  </div>
                  <div>
                    <p className="text-xs sm:text-sm font-semibold text-slate-100">{selectedChild} ({caseId})</p>
                    <p className="text-[10px] text-slate-400">Live API WebSocket · Encrypted</p>
                  </div>
                </div>
                {childrenWithChats.find((c: any) => c.id === selectedChild) && (
                  <RiskBadge level={(childrenWithChats.find((c: any) => c.id === selectedChild)!.riskLevel || 'high') as any} />
                )}
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                <div className="text-center mb-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5">
                    <Shield size={10} className="text-emerald-400" />
                    <span className="text-[10px] text-slate-500">Messages are protected and audited per POCSO Act</span>
                  </div>
                </div>

                {currentMessages.map((msg) => {
                  const isModerator = msg.senderRole === 'moderator';
                  return (
                    <div key={msg.id} className={`flex ${isModerator ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[70%] ${isModerator ? 'order-2' : ''}`}>
                        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                          isModerator
                            ? 'bg-cyan-500/15 text-cyan-50 rounded-br-md'
                            : 'bg-white/5 text-slate-300 rounded-bl-md'
                        }`}>
                          {msg.content}
                        </div>
                        <p className={`text-[9px] text-slate-600 mt-1 ${isModerator ? 'text-right' : ''}`}>
                          {isModerator ? 'You' : selectedChild} · {timeAgo(msg.timestamp)}
                        </p>
                      </div>
                    </div>
                  );
                })}

                {currentMessages.length === 0 && (
                  <div className="text-center py-16">
                    <MessageSquare size={32} className="text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">No messages yet</p>
                  </div>
                )}

                <div ref={bottomRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t border-white/5">
                <div className="flex items-center gap-2">
                  <button className="p-2.5 rounded-xl hover:bg-white/5 text-slate-500 hover:text-slate-300 transition-all">
                    <Paperclip size={18} />
                  </button>
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type a confidential message..."
                    className="input-field flex-1"
                  />
                  <button
                    onClick={handleSend}
                    disabled={!message.trim()}
                    className={`p-2.5 rounded-xl transition-all ${
                      message.trim()
                        ? 'bg-cyan-500 text-white hover:bg-cyan-400'
                        : 'bg-white/5 text-slate-600'
                    }`}
                  >
                    <Send size={18} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
