'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ScheduleService } from '@/services/schedule.service';
import { AvailabilitySlot } from '@/types/schedule';
import { useAppContext } from '@/context/app-context';

const STATUS_CONFIG: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  available:  { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-400', label: 'Available'  },
  booked:     { bg: 'bg-blue-50',    text: 'text-blue-700',    dot: 'bg-blue-400',    label: 'Booked'     },
  blocked:    { bg: 'bg-amber-50',   text: 'text-amber-700',   dot: 'bg-amber-400',   label: 'Blocked'    },
  cancelled:  { bg: 'bg-red-50',     text: 'text-red-600',     dot: 'bg-red-400',     label: 'Cancelled'  },
};

const fmt = (t: string) => t.substring(0, 5);

const todayISO = () => new Date().toISOString().split('T')[0];

const displayDate = (iso: string) => {
  const [y, m, d] = iso.split('-');
  return `${d} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+m-1]} ${y}`;
};

export default function SchedulesPage() {
  const [slots, setSlots]       = useState<AvailabilitySlot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [date, setDate]         = useState(todayISO);
  const { professionalId }      = useAppContext();

  const fetchSlots = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await ScheduleService.getDaySchedule(professionalId, date);
      setSlots(data.entries ?? []);
    } catch (err) {
      console.error('Failed to fetch slots:', err);
      setSlots([]);
    } finally {
      setIsLoading(false);
    }
  }, [professionalId, date]);

  useEffect(() => { fetchSlots(); }, [fetchSlots]);

  const available = slots.filter(s => s.status === 'available').length;
  const booked    = slots.filter(s => s.status === 'booked').length;

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">

        {/* ── Page header ── */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Schedules</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your availability and view upcoming slots.</p>
        </div>

        {/* ── Toolbar ── */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {/* Date picker — styled with explicit white bg so it's always visible */}
            <div className="relative">
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="
                  bg-white text-gray-800 text-sm font-medium
                  border border-gray-200 rounded-xl
                  px-4 py-2.5 pr-10
                  shadow-sm
                  focus:outline-none focus:ring-2 focus:ring-green-400 focus:border-transparent
                  cursor-pointer
                  appearance-none
                "
              />
              {/* Calendar icon overlay */}
              <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                  <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
                  <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
              </div>
            </div>

            <button
              onClick={fetchSlots}
              className="flex items-center gap-2 bg-white text-gray-600 text-sm font-medium border border-gray-200 rounded-xl px-4 py-2.5 shadow-sm hover:bg-gray-50 transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              Refresh
            </button>
          </div>

          <button className="flex items-center gap-2 bg-green-500 hover:bg-green-600 text-white text-sm font-semibold rounded-xl px-5 py-2.5 shadow-sm transition-colors">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            New Slot
          </button>
        </div>

        {/* ── Stat chips ── */}
        {!isLoading && slots.length > 0 && (
          <div className="flex gap-3 mb-5">
            <div className="bg-white border border-gray-200 rounded-xl px-4 py-2.5 shadow-sm flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-gray-400 inline-block" />
              <span className="text-sm text-gray-600 font-medium">{slots.length} total</span>
            </div>
            {available > 0 && (
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-2.5 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                <span className="text-sm text-emerald-700 font-medium">{available} available</span>
              </div>
            )}
            {booked > 0 && (
              <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-2.5 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
                <span className="text-sm text-blue-700 font-medium">{booked} booked</span>
              </div>
            )}
          </div>
        )}

        {/* ── Table card ── */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          {/* Card header */}
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-700">{displayDate(date)}</span>
            {isLoading && (
              <span className="text-xs text-gray-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce inline-block" style={{animationDelay:'0ms'}}/>
                <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce inline-block" style={{animationDelay:'150ms'}}/>
                <span className="w-1.5 h-1.5 rounded-full bg-gray-300 animate-bounce inline-block" style={{animationDelay:'300ms'}}/>
              </span>
            )}
          </div>

          <table className="w-full text-left">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-widest">Time</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-widest">Status</th>
                <th className="px-6 py-3 text-[11px] font-semibold text-gray-400 uppercase tracking-widest text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                // Skeleton rows
                [1,2,3].map(i => (
                  <tr key={i}>
                    <td className="px-6 py-4"><div className="h-4 w-28 bg-gray-100 rounded animate-pulse" /></td>
                    <td className="px-6 py-4"><div className="h-5 w-20 bg-gray-100 rounded-full animate-pulse" /></td>
                    <td className="px-6 py-4 text-right"><div className="h-4 w-24 bg-gray-100 rounded animate-pulse ml-auto" /></td>
                  </tr>
                ))
              ) : slots.length === 0 ? (
                <tr>
                  <td colSpan={3} className="px-6 py-16 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
                        <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                      </svg>
                      <p className="text-sm text-gray-400">No slots for this date</p>
                    </div>
                  </td>
                </tr>
              ) : (
                slots.map((slot) => {
                  const cfg = STATUS_CONFIG[slot.status] ?? STATUS_CONFIG['available'];
                  return (
                    <tr key={slot.slot_id} className="hover:bg-gray-50 transition-colors group">
                      <td className="px-6 py-4">
                        <span className="text-sm font-semibold text-gray-800 tabular-nums">
                          {fmt(slot.start_time)} – {fmt(slot.end_time)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${cfg.bg} ${cfg.text}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
                          {cfg.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button className="text-xs font-semibold text-gray-400 hover:text-gray-700 transition-colors px-3 py-1.5 rounded-lg hover:bg-gray-100 mr-1">
                          Edit
                        </button>
                        <button className="text-xs font-semibold text-red-400 hover:text-red-600 transition-colors px-3 py-1.5 rounded-lg hover:bg-red-50">
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}