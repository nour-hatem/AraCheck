"use client";

import { useState, KeyboardEvent, useRef, useEffect } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  SendHorizontal,
  CornerDownLeft,
  Mic,
  Square,
  Loader2,
  ImagePlus,
  X,
  Globe,
} from "lucide-react";

interface SendPayload {
  /** Text shown in the user's chat bubble */
  display: string;
  /** Full text sent to the API (may include hidden image/audio context) */
  full: string;
}

interface TextInputProps {
  onSend: (payload: SendPayload) => void;
  disabled: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function TextInput({ onSend, disabled }: TextInputProps) {
  const [value, setValue] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [voiceLang, setVoiceLang] = useState<"ar" | "en">("ar");

  // ── Image state ──────────────────────────────────────────────────
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [isAnalyzingImage, setIsAnalyzingImage] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 144) + "px";
  }, [value]);

  const handleSend = async () => {
    const trimmed = value.trim();
    if (disabled) return;

    // If an image is attached, analyze it first then send
    if (imageFile) {
      await analyzeAndSend(trimmed);
      return;
    }

    if (!trimmed) return;
    // Plain text: display === full (no hidden context)
    onSend({ display: trimmed, full: trimmed });
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Image Upload ─────────────────────────────────────────────────
  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => {
      setImagePreview(ev.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Reset input so same file can be re-selected
    e.target.value = "";
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const analyzeAndSend = async (textMessage: string) => {
    if (!imageFile) return;
    setIsAnalyzingImage(true);

    // What the user sees in the bubble — only their typed text (or a generic label)
    const displayText = textMessage || "📷 صورة طبية";

    try {
      const formData = new FormData();
      formData.append("file", imageFile);

      const res = await fetch(`${API_URL}/analyze-image`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail ?? `status ${res.status}`);
      }

      const data = await res.json();

      // Full text sent to the model (hidden from the user's bubble)
      let fullText = textMessage || "حللي هذه الصورة الطبية.";
      if (data.extracted_text) {
        fullText += `\n\n[نص مستخرج من الصورة]: ${data.extracted_text}`;
      }
      if (data.visual_description) {
        fullText += `\n\n[وصف بصري للصورة]: ${data.visual_description}`;
      }
      if (data.error) {
        fullText += `\n\n[ملاحظة تقنية]: ${data.error}`;
      }

      // display = what the user sees, full = what the model gets
      onSend({ display: displayText, full: fullText });
      setValue("");
      removeImage();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error("Image analysis error:", msg);
      // On error, send as-is with no hidden context
      onSend({
        display: displayText,
        full: (textMessage || "حللي هذه الصورة الطبية.") + `\n\n[خطأ في تحليل الصورة: ${msg}]`,
      });
      setValue("");
      removeImage();
    } finally {
      setIsAnalyzingImage(false);
    }
  };

  // ── Voice Recording ───────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await sendForTranscription(blob);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const sendForTranscription = async (blob: Blob) => {
    setIsTranscribing(true);
    try {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");
      formData.append("language", voiceLang);
      const res = await fetch(`${API_URL}/transcribe`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`status ${res.status}`);
      const data = await res.json();
      if (data.text) {
        setValue((prev) => (prev ? prev + " " + data.text : data.text));
        textareaRef.current?.focus();
      }
    } catch (err) {
      console.error("Transcription error:", err);
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleMicClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const isBusy = disabled || isTranscribing || isAnalyzingImage;
  const canSend = !isBusy && (!!value.trim() || !!imageFile);

  const sendLabel = isAnalyzingImage
    ? "جاري تحليل الصورة..."
    : "إرسال";

  return (
    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200/80 dark:border-slate-800/80 p-3 sm:p-4 sticky bottom-0 z-10 shadow-lg transition-colors duration-300">
      <div className="max-w-3xl mx-auto flex flex-col gap-2">

        {/* Image Preview Strip */}
        {imagePreview && (
          <div className="flex items-center gap-2 px-1">
            <div className="relative group w-16 h-16 rounded-xl overflow-hidden border border-teal-400/40 shadow-sm shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={imagePreview}
                alt="معاينة الصورة"
                className="w-full h-full object-cover"
              />
              <button
                onClick={removeImage}
                className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"
                title="حذف الصورة"
              >
                <X className="w-4 h-4 text-white" />
              </button>
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {isAnalyzingImage ? (
                <span className="flex items-center gap-1 text-teal-600 dark:text-teal-400">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  جاري تحليل الصورة...
                </span>
              ) : (
                "صورة مرفقة — اكتب سؤالك أو اضغط إرسال مباشرة"
              )}
            </span>
          </div>
        )}

        <div className="relative flex items-end gap-2 bg-slate-50 dark:bg-slate-950/80 border border-slate-300/80 dark:border-slate-800 focus-within:border-teal-500 dark:focus-within:border-teal-400 focus-within:ring-2 focus-within:ring-teal-500/20 rounded-2xl p-2 transition-all shadow-xs">

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp"
            className="hidden"
            onChange={handleImageSelect}
          />

          {/* Image Upload Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={isBusy}
            title="إرفاق صورة طبية"
            className={`h-10 w-10 rounded-xl shrink-0 transition-all ${
              imageFile
                ? "text-teal-600 bg-teal-50 dark:bg-teal-950/40"
                : "text-slate-400 hover:text-teal-600 hover:bg-teal-50 dark:hover:bg-teal-950/40"
            }`}
          >
            <ImagePlus className="w-4 h-4" />
          </Button>

          {/* Mic Button */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleMicClick}
            disabled={isBusy}
            title={isRecording ? "إيقاف التسجيل" : "تسجيل صوتي"}
            className={`h-10 w-10 rounded-xl shrink-0 transition-all ${
              isRecording
                ? "bg-red-500 hover:bg-red-600 text-white animate-pulse shadow-md shadow-red-400/30"
                : "text-slate-400 hover:text-teal-600 hover:bg-teal-50 dark:hover:bg-teal-950/40"
            }`}
          >
            {isTranscribing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : isRecording ? (
              <Square className="w-4 h-4 fill-current" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </Button>

          {/* Voice Language Selector Button */}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setVoiceLang((prev) => (prev === "ar" ? "en" : "ar"))}
            disabled={isBusy}
            title={voiceLang === "ar" ? "لغة الصوت الحالية: العربية (اضغط للتحويل إلى الإنجليزية)" : "Current Voice Language: English (Click to switch to Arabic)"}
            className="h-10 px-2.5 rounded-xl text-xs font-bold shrink-0 transition-all text-teal-700 bg-teal-50 dark:bg-teal-950/50 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900/60 border border-teal-200/60 dark:border-teal-800/60 flex items-center gap-1"
          >
            <Globe className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
            <span>{voiceLang === "ar" ? "عربي" : "EN"}</span>
          </Button>

          {/* Text Area */}
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRecording
                ? "🔴 جاري التسجيل... اضغط على الميكروفون للإيقاف"
                : isTranscribing
                ? "⏳ جاري تحويل الصوت لنص..."
                : isAnalyzingImage
                ? "⏳ جاري تحليل الصورة..."
                : imageFile
                ? "اكتب سؤالك عن الصورة أو اضغط إرسال..."
                : "اكتب سؤالك أو استفسارك الطبي هنا..."
            }
            disabled={isBusy}
            rows={1}
            className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 text-sm sm:text-base resize-none min-h-[44px] max-h-36 py-2.5 px-2"
          />

          {/* Send Button */}
          <Button
            onClick={handleSend}
            disabled={!canSend}
            className="h-10 px-4 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-medium shadow-md shadow-teal-500/20 disabled:opacity-40 transition-all shrink-0 cursor-pointer gap-1.5"
          >
            {isAnalyzingImage ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <span className="text-xs sm:text-sm font-semibold">{sendLabel}</span>
                <SendHorizontal className="w-4 h-4 rotate-180" />
              </>
            )}
          </Button>
        </div>

        {/* Keyboard hint & Disclaimer */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 px-2">
          <span className="hidden sm:inline-flex items-center gap-1">
            <CornerDownLeft className="w-3 h-3 text-slate-400 dark:text-slate-500" />
            اضغط{" "}
            <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[10px] text-slate-600 dark:text-slate-300">
              Enter
            </kbd>{" "}
            للإرسال، و{" "}
            <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[10px] text-slate-600 dark:text-slate-300">
              Shift+Enter
            </kbd>{" "}
            لسطر جديد
          </span>
          <span className="w-full text-center sm:text-left text-slate-400 dark:text-slate-500">
            * هذا النظام يقدم إرشادات عامة ولا يغني عن الطبيب.
          </span>
        </div>
      </div>
    </div>
  );
}