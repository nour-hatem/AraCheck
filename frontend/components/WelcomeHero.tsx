"use client";

import { Sparkles, Bot, ShieldAlert, HeartPulse, Apple, Pill, Activity } from "lucide-react";

interface WelcomeHeroProps {
  onSelectSuggestion: (prompt: string) => void;
}

export function WelcomeHero({ onSelectSuggestion }: WelcomeHeroProps) {
  const suggestions = [
    {
      title: "نزلات البرد والفيروسات",
      desc: "ما هي الأغذية والنصائح الوقائية لتسريع التعافي من نزلات البرد؟",
      icon: HeartPulse,
      color: "from-teal-500 to-emerald-500",
      bgColor: "bg-teal-50/70 dark:bg-teal-950/30 border-teal-100 dark:border-teal-900/40 hover:border-teal-300 dark:hover:border-teal-700",
    },
    {
      title: "المضادات الحيوية",
      desc: "هل تناول المضادات الحيوية مفيد في علاج العدوى الفيروسية؟",
      icon: Pill,
      color: "from-blue-500 to-cyan-500",
      bgColor: "bg-blue-50/70 dark:bg-blue-950/30 border-blue-100 dark:border-blue-900/40 hover:border-blue-300 dark:hover:border-blue-700",
    },
    {
      title: "التغذية والمناعة",
      desc: "ما هي الأطعمة الصحية الأكثر فاعلية في تقوية جهاز المناعة؟",
      icon: Apple,
      color: "from-emerald-500 to-green-500",
      bgColor: "bg-emerald-50/70 dark:bg-emerald-950/30 border-emerald-100 dark:border-emerald-900/40 hover:border-emerald-300 dark:hover:border-emerald-700",
    },
    {
      title: "صحة ضغط الدم",
      desc: "كيف يمكن المحافظة على قراءات ضغط الدم المتوازنة؟",
      icon: Activity,
      color: "from-indigo-500 to-blue-500",
      bgColor: "bg-indigo-50/70 dark:bg-indigo-950/30 border-indigo-100 dark:border-indigo-900/40 hover:border-indigo-300 dark:hover:border-indigo-700",
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center my-auto py-8 px-4 text-center max-w-3xl mx-auto w-full animate-in fade-in duration-500">
      {/* Icon Badge */}
      <div className="relative mb-4">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500 via-emerald-600 to-cyan-600 flex items-center justify-center text-white shadow-lg shadow-teal-500/25">
          <Bot className="w-9 h-9" />
        </div>
        <div className="absolute -bottom-1 -right-1 bg-amber-400 p-1 rounded-full text-slate-900 shadow-xs">
          <Sparkles className="w-3.5 h-3.5" />
        </div>
      </div>

      {/* Main Title */}
      <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight mb-2">
        مرحباً بك في <span className="bg-gradient-to-r from-teal-600 to-emerald-500 dark:from-teal-400 dark:to-emerald-400 bg-clip-text text-transparent">AraCheck</span>
      </h2>

      {/* Subtitle */}
      <p className="text-slate-600 dark:text-slate-400 text-sm sm:text-base max-w-lg mb-8 leading-relaxed">
        المساعد الذكي المخصص للإجابة والاستكشاف الأولي للاستفسارات والمعلومات الطبية باللغة العربية.
      </p>

      {/* Suggestion Prompt Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-right">
        {suggestions.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectSuggestion(item.desc)}
              className={`flex items-start gap-3 p-4 rounded-xl border transition-all duration-200 text-right cursor-pointer hover:shadow-md ${item.bgColor}`}
            >
              <div className={`p-2.5 rounded-lg bg-gradient-to-br ${item.color} text-white shrink-0 shadow-xs`}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-0.5">{item.title}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">{item.desc}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Security/Privacy Note */}
      <div className="mt-8 flex items-center justify-center gap-2 text-xs text-slate-400 dark:text-slate-500">
        <ShieldAlert className="w-4 h-4 text-slate-400 dark:text-slate-500" />
        <span>جميع الاستفسارات تُعالج بخصوصية تامة لأغراض الاسترشاد والتوعية الطبية.</span>
      </div>
    </div>
  );
}
