"use client";

import { useState, useRef, useEffect } from "react";

interface RecorderCardProps {
  disabled?: boolean;
  onFile: (file: File) => void;
}

export default function RecorderCard({ disabled, onFile }: RecorderCardProps) {
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [mediaSupported, setMediaSupported] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chunks = useRef<Blob[]>([]);

  useEffect(() => {
    // Check if MediaRecorder is supported
    if (!window.MediaRecorder) {
      setMediaSupported(false);
    }
  }, []);

  const startRecording = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      chunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        const file = new File([blob], "recording.webm", { type: "audio/webm" });
        onFile(file);

        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setRecording(true);
    } catch (err) {
      console.error("Recording error:", err);
      if (err instanceof Error) {
        if (err.name === "NotAllowedError") {
          setError("Microphone access denied. Please allow microphone permissions.");
        } else if (err.name === "NotFoundError") {
          setError("No microphone found. Please connect a microphone and try again.");
        } else {
          setError("Failed to start recording. Please try again.");
        }
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && recording) {
      mediaRecorder.stop();
      setRecording(false);
      setMediaRecorder(null);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith("audio/")) {
      onFile(file);
    } else {
      setError("Please select a valid audio file.");
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border p-6 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Audio Recording</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {mediaSupported ? (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <button
              onClick={startRecording}
              disabled={disabled || recording}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors flex items-center gap-2"
            >
              {recording ? (
                <>
                  <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                  Recording...
                </>
              ) : (
                "Start Recording"
              )}
            </button>

            <button
              onClick={stopRecording}
              disabled={!recording}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
            >
              Stop
            </button>
          </div>

          {recording && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              Recording in progress...
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-gray-600 text-sm">
            Your browser doesn&apos;t support audio recording. Please upload an audio file instead.
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Audio File
            </label>
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileUpload}
              disabled={disabled}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
        </div>
      )}
    </div>
  );
}
