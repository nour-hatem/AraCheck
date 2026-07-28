"use client";

import { useState, KeyboardEvent, useRef } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SendHorizontal, CornerDownLeft } from "lucide-react";

interface TextInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export function TextInput({ onSend, disabled }: TextInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-t border-slate-200/80 dark:border-slate-800/80 p-3 sm:p-4 sticky bottom-0 z-10 shadow-lg transition-colors duration-300">
      <div className="max-w-3xl mx-auto flex flex-col gap-2">
        <div className="relative flex items-end gap-2 bg-slate-50 dark:bg-slate-950/80 border border-slate-300/80 dark:border-slate-800 focus-within:border-teal-500 dark:focus-within:border-teal-400 focus-within:ring-2 focus-within:ring-teal-500/20 rounded-2xl p-2 transition-all shadow-xs">
          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="اكتب سؤالك أو استفسارك الطبي هنا..."
            disabled={disabled}
            rows={1}
            className="flex-1 bg-transparent border-0 focus-visible:ring-0 focus-visible:ring-offset-0 text-slate-800 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 text-sm sm:text-base resize-none min-h-[44px] max-h-36 py-2.5 px-2"
          />
          <Button
            onClick={handleSend}
            disabled={disabled || !value.trim()}
            className="h-10 px-4 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-medium shadow-md shadow-teal-500/20 disabled:opacity-40 transition-all shrink-0 cursor-pointer gap-1.5"
          >
            <span className="text-xs sm:text-sm font-semibold">إرسال</span>
            <SendHorizontal className="w-4 h-4 rotate-180" />
          </Button>
        </div>

        {/* Keyboard hint & Disclaimer */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500 px-2">
          <span className="hidden sm:inline-flex items-center gap-1">
            <CornerDownLeft className="w-3 h-3 text-slate-400 dark:text-slate-500" />
            اضغط <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[10px] text-slate-600 dark:text-slate-300">Enter</kbd> للإرسال، و <kbd className="px-1 py-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[10px] text-slate-600 dark:text-slate-300">Shift+Enter</kbd> لسطر جديد
          </span>
          <span className="w-full text-center sm:text-left text-slate-400 dark:text-slate-500">
            * هذا النظام يقدم إرشادات عامة ولا يغني عن الطبيب.
          </span>
        </div>
      </div>
    </div>
  );
}