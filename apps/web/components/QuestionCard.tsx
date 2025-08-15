"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type Question = { id: number; text: string };

interface QuestionCardProps {
  question?: Question | null;
  onLoad: (question: Question) => void;
}

export default function QuestionCard({ question, onLoad }: QuestionCardProps) {
  const [loading, setLoading] = useState(false);

  async function loadQuestion() {
    setLoading(true);
    try {
      const { data } = await api.get("/questions/SWE");
      const list: Question[] = Array.isArray(data) ? data : [];
      if (list.length) {
        const randomQuestion = list[Math.floor(Math.random() * list.length)];
        onLoad(randomQuestion);
      }
    } catch (error) {
      console.error("Failed to load question:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Interview Question</h2>
        {question && (
          <span className="text-sm px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">
            #{question.id}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={loadQuestion}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {loading ? "Loading..." : "Load Question"}
        </button>
      </div>

      {question ? (
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-gray-900 leading-relaxed">{question.text}</p>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>Click &ldquo;Load Question&rdquo; to get started with your interview practice.</p>
        </div>
      )}
    </div>
  );
}
