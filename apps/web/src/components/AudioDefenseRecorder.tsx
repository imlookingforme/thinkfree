import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Globe, Sparkles, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';

interface AudioDefenseRecorderProps {
  sessionId: string;
  onDefenseComplete?: (result: any) => void;
}

export const AudioDefenseRecorder: React.FC<AudioDefenseRecorderProps> = ({
  sessionId,
  onDefenseComplete,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [language, setLanguage] = useState('en');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [telemetry, setTelemetry] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const timerRef = useRef<any>(null);
  const speechRecognitionRef = useRef<any>(null);

  // Supported Indic Languages via Bhashini ASR
  const languages = [
    { code: 'en', label: 'English' },
    { code: 'hi', label: 'Hindi (हिंदी)' },
    { code: 'ta', label: 'Tamil (தமிழ்)' },
    { code: 'te', label: 'Telugu (తెలుగు)' },
    { code: 'kn', label: 'Kannada (ಕನ್ನಡ)' },
    { code: 'bn', label: 'Bengali (বাংলা)' },
    { code: 'mr', label: 'Marathi (मराठी)' },
  ];

  // Draw Audio Visualizer
  const drawWaveform = () => {
    if (!canvasRef.current || !analyserRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      animationFrameRef.current = requestAnimationFrame(render);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
        gradient.addColorStop(0, '#3b82f6');
        gradient.addColorStop(1, '#06b6d4');

        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 2;
      }
    };
    render();
  };

  const startRecording = async () => {
    try {
      setError(null);
      setTranscript('');
      setTelemetry(null);
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Audio Context for visualizer
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;
      drawWaveform();

      // MediaRecorder for audio blob
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      // Web Speech API for real-time transcription
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = language === 'hi' ? 'hi-IN' : language === 'ta' ? 'ta-IN' : 'en-US';

        recognition.onresult = (event: any) => {
          let currentTranscript = '';
          for (let i = 0; i < event.results.length; i++) {
            currentTranscript += event.results[i][0].transcript + ' ';
          }
          setTranscript(currentTranscript.trim());
        };

        recognition.onerror = (e: any) => {
          console.warn('Speech recognition warning:', e);
        };

        recognition.start();
        speechRecognitionRef.current = recognition;
      }
    } catch (err: any) {
      console.error('Audio capture error:', err);
      setError('Microphone access denied or unavailable. You can also type or use speech input.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }

    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch (e) {
        // ignore
      }
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    setIsRecording(false);
  };

  const submitDefense = async () => {
    if (!transcript && audioChunksRef.current.length === 0) {
      setError('Please record your spoken defense before submitting.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // If we have an audio blob, transcribe with server / Bhashini
      let finalTranscript = transcript;
      if (audioChunksRef.current.length > 0) {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'defense.webm');
        formData.append('language', language);

        try {
          const transcribeRes = await apiClient.postForm('/validations/transcribe', formData);
          if (transcribeRes.data?.transcript) {
            finalTranscript = transcribeRes.data.transcript;
            setTranscript(finalTranscript);
          }
          if (transcribeRes.data?.fluency_telemetry) {
            setTelemetry(transcribeRes.data.fluency_telemetry);
          }
        } catch (e) {
          console.warn('Backend audio transcription fallback, using speech recognition transcript', e);
        }
      }

      // Submit verbal defense for rubric grading
      const res = await apiClient.post(`/validations/${sessionId}/explain-audio`, {
        transcript: finalTranscript || 'Spoken defense completed.',
        language,
        duration_seconds: Math.max(5, recordingTime),
      });

      if (onDefenseComplete) {
        onDefenseComplete(res.data);
      }
    } catch (err: any) {
      console.error('Defense submission failed:', err);
      setError(err?.message || 'Failed to grade verbal defense. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-lg">
            <Mic className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Live Spoken Defense & STT</h3>
            <p className="text-xs text-slate-400">
              Articulate your logic, time complexity, and edge cases verbally
            </p>
          </div>
        </div>

        {/* Language selector for Bhashini */}
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-slate-400" />
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={isRecording}
            className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 text-red-400 text-xs rounded-lg">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Waveform Visualizer & Timer */}
      <div className="relative bg-slate-950 border border-slate-800/80 rounded-xl p-4 flex flex-col items-center justify-center min-h-[140px] overflow-hidden">
        <canvas
          ref={canvasRef}
          width={400}
          height={80}
          className="w-full h-20 max-w-md opacity-90"
        />

        {isRecording && (
          <div className="absolute top-3 right-3 flex items-center gap-2 px-2.5 py-1 bg-red-500/20 text-red-400 border border-red-500/30 rounded-full text-xs font-mono animate-pulse">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span>{Math.floor(recordingTime / 60)}:{String(recordingTime % 60).padStart(2, '0')}</span>
          </div>
        )}

        {!isRecording && recordingTime > 0 && (
          <div className="absolute top-3 right-3 px-2.5 py-1 bg-slate-800 text-slate-300 rounded-full text-xs font-mono">
            Recorded {recordingTime}s
          </div>
        )}
      </div>

      {/* Recording Controls */}
      <div className="flex items-center justify-center gap-4">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-blue-500/20"
          >
            <Mic className="w-4 h-4" />
            <span>Start Speaking</span>
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="flex items-center gap-2 px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-red-500/20"
          >
            <Square className="w-4 h-4" />
            <span>Finish Speaking</span>
          </button>
        )}
      </div>

      {/* Live Transcript / Review Textarea */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Real-time Voice Transcript
          </span>
          {transcript && (
            <span>{transcript.split(/\s+/).filter(Boolean).length} words</span>
          )}
        </div>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="Your spoken words will transcribe here in real-time. You can also edit or refine before final submission..."
          rows={3}
          className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500/60 transition-colors"
        />
      </div>

      {/* Telemetry Pills if Available */}
      {telemetry && (
        <div className="grid grid-cols-3 gap-2 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs">
          <div>
            <span className="text-slate-500 block">Cadence</span>
            <span className="text-slate-200 font-semibold">{telemetry.words_per_minute} WPM</span>
          </div>
          <div>
            <span className="text-slate-500 block">Hesitation</span>
            <span className="text-slate-200 font-semibold">{Math.round(telemetry.hesitation_ratio * 100)}%</span>
          </div>
          <div>
            <span className="text-slate-500 block">Concepts</span>
            <span className="text-blue-400 font-semibold">
              {telemetry.detected_keywords?.length || 0} detected
            </span>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end pt-2">
        <button
          onClick={submitDefense}
          disabled={isSubmitting || (!transcript && recordingTime === 0)}
          className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-xs font-semibold transition-colors shadow-lg shadow-emerald-500/10"
        >
          {isSubmitting ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Analyzing Comprehension...</span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Submit Verbal Defense</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
