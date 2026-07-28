"use client";

import { Stethoscope, Trash2, PanelRightOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  onClear: () => void;
  hasMessages: boolean;
  isMockMode: boolean;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export function Header({
  onClear,
  hasMessages,
  isMockMode,
  isSidebarOpen,
  onToggleSidebar,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-10 backdrop-blur-md bg-white/80 dark:bg-slate-900/80 border-b border-slate-200/80 dark:border-slate-800/80 px-4 py-3 shadow-xs transition-colors duration-300">
      <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
        {/* Left/Right Logo & Sidebar Toggle */}
        <div className="flex items-center gap-3">
          {/* Sidebar Toggle Button */}
          <Button
            variant="outline"
            size="icon"
            onClick={onToggleSidebar}
            className="w-9 h-9 rounded-xl border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            title={isSidebarOpen ? "إخفاء القائمة الجانبية" : "عرض القائمة الجانبية (المحادثات السابقة)"}
          >
            <PanelRightOpen className="w-4 h-4" />
          </Button>

          {/* Logo & Brand */}
          <div className="flex items-center gap-2.5">
            <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 text-white shadow-md shadow-teal-500/20">
              <Stethoscope className="w-4.5 h-4.5 stroke-[2.2]" />
              <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-teal-500 border-2 border-white dark:border-slate-900"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-lg font-bold bg-gradient-to-r from-teal-600 via-emerald-500 to-teal-400 dark:from-teal-400 dark:via-emerald-400 dark:to-teal-300 bg-clip-text text-transparent tracking-wide">
                  AraCheck
                </h1>
                <span className="text-[10px] px-1.5 py-0.2 rounded-full font-medium bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200/60 dark:border-teal-800/60">
                  أراشيك
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
                المساعد الذكي لفحص الاستفسارات الطبية
              </p>
            </div>
          </div>
        </div>

        {/* Right Status & Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Theme Toggle Button */}
          <ThemeToggle />

          {/* Mode Indicator */}
          <div className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
            isMockMode
              ? "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800/60"
              : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/60"
          }`}>
            <span className={`w-2 h-2 rounded-full ${isMockMode ? "bg-amber-500 animate-pulse" : "bg-emerald-500"}`} />
            {isMockMode ? "وضع التجربة (Mock API)" : "متصل بالخادم (Live API)"}
          </div>

          {/* Clear Button */}
          {hasMessages && (
            <Button
              variant="outline"
              size="sm"
              onClick={onClear}
              className="text-xs text-slate-600 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 border-slate-200 dark:border-slate-800 transition-colors gap-1.5 rounded-lg cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">مسح</span>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
