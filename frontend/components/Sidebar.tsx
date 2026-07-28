"use client";

import { useState } from "react";
import { Conversation, UserProfile } from "@/lib/types";
import {
  Plus,
  MessageSquare,
  Trash2,
  Edit2,
  Check,
  X,
  Settings,
  PanelRightClose,
  Stethoscope,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  onRename: (id: string, newTitle: string) => void;
  user: UserProfile;
  onOpenUserModal: () => void;
}

export function Sidebar({
  isOpen,
  onToggle,
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  onRename,
  user,
  onOpenUserModal,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const handleStartRename = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleSaveRename = (id: string, e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (editTitle.trim()) {
      onRename(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onToggle}
          className="md:hidden fixed inset-0 z-30 bg-slate-900/50 backdrop-blur-xs transition-opacity"
        />
      )}

      {/* Main Sidebar Container */}
      <aside
        className={`fixed md:static top-0 right-0 z-40 h-full bg-slate-100/90 dark:bg-slate-900 text-slate-800 dark:text-slate-100 border-l border-slate-200/90 dark:border-slate-800 flex flex-col transition-all duration-300 ease-in-out shadow-2xl md:shadow-none ${
          isOpen ? "w-72 translate-x-0" : "w-0 -translate-x-full md:translate-x-0 md:w-0 md:border-l-0 overflow-hidden"
        }`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-200/90 dark:border-slate-800 flex items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-teal-600 to-emerald-500 text-white flex items-center justify-center font-bold">
              <Stethoscope className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-900 dark:text-slate-100">المحادثات الطبية</h2>
              <p className="text-[10px] text-slate-500 dark:text-slate-400">سجل الاستفسارات السابقة</p>
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="w-8 h-8 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-200/80 dark:hover:bg-slate-800 transition-colors"
            title="إغلاق القائمة الجانبية"
          >
            <PanelRightClose className="w-4 h-4" />
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="p-3 shrink-0">
          <Button
            onClick={onNewChat}
            className="w-full bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-medium text-xs py-2.5 rounded-xl shadow-md shadow-teal-600/20 flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>محادثة جديدة</span>
          </Button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800">
          {conversations.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400 dark:text-slate-500 px-4">
              لا توجد محادثات سابقة حتى الآن. انقر على "محادثة جديدة" للبدء.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeId;
              const isEditing = conv.id === editingId;

              return (
                <div
                  key={conv.id}
                  onClick={() => onSelect(conv.id)}
                  className={`group relative flex items-center justify-between p-2.5 rounded-xl text-xs transition-all cursor-pointer ${
                    isActive
                      ? "bg-teal-50/90 dark:bg-teal-950/60 text-teal-800 dark:text-teal-300 font-semibold border border-teal-200/80 dark:border-teal-800/80 shadow-2xs"
                      : "text-slate-600 dark:text-slate-300 hover:bg-slate-200/60 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? "text-teal-600 dark:text-teal-400" : "text-slate-400 dark:text-slate-500"}`} />
                    
                    {isEditing ? (
                      <form
                        onSubmit={(e) => handleSaveRename(conv.id, e)}
                        className="flex items-center gap-1 flex-1 min-w-0"
                      >
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          autoFocus
                          className="w-full bg-white dark:bg-slate-950 text-slate-900 dark:text-white px-2 py-1 rounded text-xs border border-teal-500 focus:outline-hidden"
                        />
                        <button
                          type="submit"
                          onClick={(e) => handleSaveRename(conv.id, e)}
                          className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 p-0.5"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={handleCancelRename}
                          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </form>
                    ) : (
                      <span className="truncate flex-1 text-right">{conv.title}</span>
                    )}
                  </div>

                  {/* Actions (Rename & Delete) */}
                  {!isEditing && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                      <button
                        onClick={(e) => handleStartRename(conv, e)}
                        className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700/60 rounded transition-colors"
                        title="إعادة تسمية"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(conv.id);
                        }}
                        className="p-1 text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-slate-200 dark:hover:bg-slate-700/60 rounded transition-colors"
                        title="حذف المحادثة"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* User Account Footer Trigger */}
        <div className="p-3 border-t border-slate-200/90 dark:border-slate-800 shrink-0">
          <button
            onClick={onOpenUserModal}
            className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-slate-200/70 dark:hover:bg-slate-800 transition-colors text-right cursor-pointer"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
                {user.name.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">{user.name}</p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <Settings className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />
          </button>
        </div>
      </aside>
    </>
  );
}
