"use client";

import { API_BASE } from "@/lib/api";
import type { ReportJson } from "@/lib/types";

interface ReportCardProps {
  report: ReportJson;
}

export default function ReportCard({ report }: ReportCardProps) {
  const formatScore = (score: number) => {
    return Math.round(score * 100) / 100;
  };

  const getOverallColor = (overall: number) => {
    if (overall >= 8) return "text-green-600";
    if (overall >= 6) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Analysis Report</h2>
        <a
          href={`${API_BASE}/report/${report.session_id}/pdf`}
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors text-sm"
        >
          Download PDF
        </a>
      </div>

      {/* Overall Score - Prominent Display */}
      <div className="text-center py-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600 mb-1">Overall Score</p>
        <p className={`text-4xl font-bold ${getOverallColor(report.overall)}`}>
          {formatScore(report.overall)}/10
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <p className="text-sm text-blue-600 mb-1">Words per Minute</p>
          <p className="text-2xl font-semibold text-blue-900">{report.wpm}</p>
        </div>

        <div className="bg-green-50 rounded-lg p-4 text-center">
          <p className="text-sm text-green-600 mb-1">Coverage Score</p>
          <p className="text-2xl font-semibold text-green-900">
            {formatScore(report.coverage_score * 100)}%
          </p>
        </div>

        <div className="bg-purple-50 rounded-lg p-4 text-center">
          <p className="text-sm text-purple-600 mb-1">Filler Words</p>
          <p className="text-2xl font-semibold text-purple-900">{report.filler_total}</p>
        </div>

        <div className="bg-orange-50 rounded-lg p-4 text-center">
          <p className="text-sm text-orange-600 mb-1">Session ID</p>
          <p className="text-lg font-semibold text-orange-900">#{report.session_id}</p>
        </div>
      </div>

      {/* Matched Key Points */}
      {report.matched.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-900">Key Points Covered</h3>
          <div className="flex flex-wrap gap-2">
            {report.matched.map((point, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
              >
                {point}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      {report.tips.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-medium text-gray-900">Improvement Tips</h3>
          <ul className="space-y-2">
            {report.tips.map((tip, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Session Info */}
      <div className="pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Analysis completed on {new Date(report.created_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}
