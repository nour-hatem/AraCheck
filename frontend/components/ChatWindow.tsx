"use client";

import { useEffect, useRef, useState } from "react";
import { Message } from "@/lib/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { WelcomeHero } from "./WelcomeHero";
import { Bot, User, Copy, Check, Sparkles } from "lucide-react";

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSelectSuggestion: (prompt: string) => void;
}

function renderFormattedContent(content: string) {
  const lines = content.split("\n");
  return lines.map((line, lineIdx) => {
    const parts = line.split(/(\*\*.*?\*\*|\*.*?\*)/g);

    return (
      <div key={lineIdx} className={line.trim() === "" ? "h-2" : ""}>
        {parts.map((part, partIdx) => {
          if (part.startsWith("**") && part.endsWith("**")) {
            return (
              <strong key={partIdx} className="font-bold text-slate-900 dark:text-slate-100">
                {part.slice(2, -2)}
              </strong>
            );
          } else if (part.startsWith("*") && part.endsWith("*")) {
            return (
              <em key={partIdx} className="text-teal-700 dark:text-teal-300 not-italic font-medium text-xs block mt-1.5 bg-teal-50/80 dark:bg-teal-950/60 px-2 py-1 rounded-md border border-teal-100/80 dark:border-teal-800/60">
                {part.slice(1, -1)}
              </em>
            );
          }
          return <span key={partIdx}>{part}</span>;
        })}
      </div>
    );
  });
}

export function ChatWindow({ messages, isLoading, onSelectSuggestion }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex flex-col justify-center overflow-y-auto">
        <WelcomeHero onSelectSuggestion={onSelectSuggestion} />
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 px-3 sm:px-6">
      <div className="flex flex-col gap-5 py-6 max-w-3xl mx-auto w-full">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300 ${
                isUser ? "flex-row-reverse" : "flex-row"
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                  isUser
                    ? "bg-slate-800 dark:bg-slate-700 text-white"
                    : "bg-gradient-to-tr from-teal-600 to-emerald-500 text-white"
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Content Container */}
              <div
                className={`group relative flex flex-col gap-1 max-w-[85%] sm:max-w-[78%] ${
                  isUser ? "items-start" : "items-start"
                }`}
              >
                {/* Role Label */}
                <div className="flex items-center gap-2 px-1 text-[11px] font-medium text-slate-400 dark:text-slate-500">
                  <span>{isUser ? "أنت" : "AraCheck"}</span>
                </div>

                {/* Bubble */}
                <div
                  className={`rounded-2xl px-4 py-3 text-sm leading-relaxed min-w-[3.5rem] shadow-2xs ${
                    isUser
                      ? "bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-tr-xs whitespace-pre-wrap break-words"
                      : "bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border border-slate-200/90 dark:border-slate-800/90 rounded-tl-xs shadow-xs"
                  }`}
                >
                  {isUser ? msg.content : renderFormattedContent(msg.content)}
                </div>

                {/* Actions (for Assistant) */}
                {!isUser && (
                  <div className="flex items-center gap-2 mt-0.5 px-1">
                    <button
                      onClick={() => handleCopy(msg.id, msg.content)}
                      className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-teal-700 dark:hover:text-teal-400 transition-colors py-0.5 px-1.5 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
                      title="نسخ النص"
                    >
                      {copiedId === msg.id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                          <span className="text-emerald-600 dark:text-emerald-400">تم النسخ</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>نسخ</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-start gap-3 animate-in fade-in duration-300">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 text-white flex items-center justify-center shrink-0 shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex flex-col gap-1">
              <div className="px-1 text-[11px] font-medium text-slate-400 dark:text-slate-500">AraCheck</div>
              <div className="rounded-2xl rounded-tl-xs px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2.5">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce"></span>
                </div>
                <span>جاري معالجة الاستفسار والتحليل الطبي...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}