import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus } from 'lucide-react';

interface StudentCohortItem {
  student_id: string;
  name: string;
  email: string;
  its: number;
  adr: number;
  streak: number;
  self_solves: number;
  ai_assisted: number;
  fast_lane_eligible: boolean;
  risk_band: 'independent' | 'moderate' | 'heavy_reliance';
}

interface CohortData {
  course_id: string;
  course_name: string;
  total_students: number;
  cohort_mean_its: number;
  cohort_mean_adr: number;
  reliance_distribution: Record<string, number>;
  students: StudentCohortItem[];
}

export const ProfessorPortalPage: React.FC = () => {
  const [selectedCourseId] = useState('demo_course_1');
  const [, setShowAssignModal] = useState(false);

  const { data: cohort } = useQuery<CohortData>({
    queryKey: ['cohort', selectedCourseId],
    queryFn: async () => {
      // Demo fallback mock for immediate preview
      return {
        course_id: 'CS_F211',
        course_name: 'CS F211 Data Structures & Algorithms',
        total_students: 4,
        cohort_mean_its: 81.2,
        cohort_mean_adr: 0.22,
        reliance_distribution: {
          independent: 3,
          moderate: 1,
          heavy_reliance: 0
        },
        students: [
          {
            student_id: 's1',
            name: 'Aarav Mehta',
            email: 'f20230101@pilani.bits-pilani.ac.in',
            its: 88.5,
            adr: 0.14,
            streak: 14,
            self_solves: 28,
            ai_assisted: 4,
            fast_lane_eligible: true,
            risk_band: 'independent'
          },
          {
            student_id: 's2',
            name: 'Diya Sharma',
            email: 'f20230202@pilani.bits-pilani.ac.in',
            its: 82.0,
            adr: 0.21,
            streak: 9,
            self_solves: 22,
            ai_assisted: 6,
            fast_lane_eligible: true,
            risk_band: 'independent'
          },
          {
            student_id: 's3',
            name: 'Rohan Gupta',
            email: 'f20230303@pilani.bits-pilani.ac.in',
            its: 79.0,
            adr: 0.24,
            streak: 7,
            self_solves: 19,
            ai_assisted: 7,
            fast_lane_eligible: false,
            risk_band: 'independent'
          },
          {
            student_id: 's4',
            name: 'Ananya Verma',
            email: 'f20230404@pilani.bits-pilani.ac.in',
            its: 68.5,
            adr: 0.42,
            streak: 3,
            self_solves: 11,
            ai_assisted: 15,
            fast_lane_eligible: false,
            risk_band: 'moderate'
          }
        ]
      };
    }
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              Instructor Administration · BITS Pilani
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {cohort?.course_name || 'Class Cohort Overview'}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Institutional tracking of authentic cognitive effort. LTI 1.3 Advantage integrated.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAssignModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:text-slate-900 rounded-xl text-xs font-semibold shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            <span>Create Assignment</span>
          </button>
        </div>
      </div>

      {/* Cohort KPI Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="text-xs text-slate-500 mb-1">Cohort Mean Independence (ITS)</div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {cohort?.cohort_mean_its} <span className="text-sm font-normal text-slate-400">/ 100</span>
          </div>
          <div className="text-xs text-emerald-600 mt-2">Class is performing in Exam-Ready bracket</div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="text-xs text-slate-500 mb-1">Cohort AI Dependency (ADR)</div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {cohort?.cohort_mean_adr}
          </div>
          <div className="text-xs text-slate-500 mt-2">78% of solutions reached unassisted</div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="text-xs text-slate-500 mb-1">Reliance Distribution</div>
          <div className="flex items-center gap-2 text-xs font-semibold mt-3">
            <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
              3 Independent
            </span>
            <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
              1 Moderate
            </span>
            <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">
              0 Critical
            </span>
          </div>
        </div>
      </div>

      {/* Student Roster Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white">Enrolled Students Performance Audit</h2>
          <span className="text-xs text-slate-400 font-mono">LTI Sync: Active</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-medium">
              <tr>
                <th className="py-3 px-6">Student</th>
                <th className="py-3 px-4">ITS Score</th>
                <th className="py-3 px-4">ADR Reliance</th>
                <th className="py-3 px-4">Self-Solves</th>
                <th className="py-3 px-4">Streak</th>
                <th className="py-3 px-4">Fast Lane</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
              {cohort?.students.map((st) => (
                <tr key={st.student_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                  <td className="py-3.5 px-6">
                    <div className="font-semibold text-slate-900 dark:text-white">{st.name}</div>
                    <div className="text-[11px] text-slate-400">{st.email}</div>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-slate-900 dark:text-white">{st.its}</td>
                  <td className="py-3.5 px-4 font-mono">{st.adr}</td>
                  <td className="py-3.5 px-4">{st.self_solves} solves</td>
                  <td className="py-3.5 px-4">{st.streak} days</td>
                  <td className="py-3.5 px-4">
                    {st.fast_lane_eligible ? (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                        Eligible (60s)
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400">Standard (180s)</span>
                    )}
                  </td>
                  <td className="py-3.5 px-6 text-right">
                    <button
                      onClick={() => alert(`Issued Ed25519 Verified Independent Badge to ${st.name}`)}
                      className="px-2.5 py-1 text-[11px] font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 rounded-lg text-slate-800 dark:text-slate-200"
                    >
                      Issue Badge
                    </button>
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
