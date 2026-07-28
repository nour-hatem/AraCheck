"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { ChatWindow } from "@/components/ChatWindow";
import { TextInput } from "@/components/TextInput";
import { Sidebar } from "@/components/Sidebar";
import { UserModal } from "@/components/UserModal";
import { Message, Conversation, UserProfile } from "@/lib/types";
import { sendMessage } from "@/lib/api";
import { AlertCircle } from "lucide-react";

const STORAGE_KEY_CONVS = "aracheck_conversations_v1";
const STORAGE_KEY_ACTIVE = "aracheck_active_conv_id_v1";
const STORAGE_KEY_USER = "aracheck_user_profile_v1";

const INITIAL_USER: UserProfile = {
  name: "د. نور حاتم",
  email: "nour.hatem@aracheck.ai",
  role: "طبيب / مستخدم متميز",
};

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [user, setUser] = useState<UserProfile>(INITIAL_USER);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isMockMode = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const savedConvs = localStorage.getItem(STORAGE_KEY_CONVS);
      const savedActive = localStorage.getItem(STORAGE_KEY_ACTIVE);
      const savedUser = localStorage.getItem(STORAGE_KEY_USER);

      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }

      if (savedConvs) {
        const parsed: Conversation[] = JSON.parse(savedConvs);
        setConversations(parsed);
        if (savedActive && parsed.some((c) => c.id === savedActive)) {
          setActiveId(savedActive);
        } else if (parsed.length > 0) {
          setActiveId(parsed[0].id);
        }
      }
    } catch (e) {
      console.error("Failed to load state from localStorage:", e);
    }
  }, []);

  // Sync to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CONVS, JSON.stringify(conversations));
      if (activeId) {
        localStorage.setItem(STORAGE_KEY_ACTIVE, activeId);
      }
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
    } catch (e) {
      console.error("Failed to save state to localStorage:", e);
    }
  }, [conversations, activeId, user]);

  const activeConversation = conversations.find((c) => c.id === activeId);
  const messages = activeConversation?.messages ?? [];

  const handleNewChat = () => {
    const newConv: Conversation = {
      id: crypto.randomUUID(),
      title: "محادثة جديدة",
      messages: [],
      updatedAt: Date.now(),
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveId(newConv.id);
    setError(null);
  };

  const handleSelectConversation = (id: string) => {
    setActiveId(id);
    setError(null);
  };

  const handleDeleteConversation = (id: string) => {
    setConversations((prev) => {
      const filtered = prev.filter((c) => c.id !== id);
      if (activeId === id) {
        setActiveId(filtered.length > 0 ? filtered[0].id : null);
      }
      return filtered;
    });
  };

  const handleRenameConversation = (id: string, newTitle: string) => {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title: newTitle } : c))
    );
  };

  const handleSend = async (content: string) => {
    let currentConvId = activeId;
    let updatedConvs = [...conversations];

    // If no active conversation exists, create one!
    if (!currentConvId || !updatedConvs.some((c) => c.id === currentConvId)) {
      const newConvId = crypto.randomUUID();
      const newConvTitle = content.length > 25 ? `${content.slice(0, 25)}...` : content;
      const newConv: Conversation = {
        id: newConvId,
        title: newConvTitle,
        messages: [],
        updatedAt: Date.now(),
      };
      updatedConvs = [newConv, ...updatedConvs];
      currentConvId = newConvId;
      setActiveId(newConvId);
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
    };

    // Update conversation messages & title if first message
    const targetConv = updatedConvs.find((c) => c.id === currentConvId)!;
    const isFirstMessage = targetConv.messages.length === 0;
    const newTitle = isFirstMessage
      ? content.length > 25
        ? `${content.slice(0, 25)}...`
        : content
      : targetConv.title;

    const newMessages = [...targetConv.messages, userMessage];

    setConversations(
      updatedConvs.map((c) =>
        c.id === currentConvId
          ? { ...c, messages: newMessages, title: newTitle, updatedAt: Date.now() }
          : c
      )
    );

    setIsLoading(true);
    setError(null);

    try {
      const reply = await sendMessage(content, targetConv.messages);
      setConversations((prev) =>
        prev.map((c) =>
          c.id === currentConvId
            ? { ...c, messages: [...c.messages, reply], updatedAt: Date.now() }
            : c
        )
      );
    } catch {
      setError(
        "لم نتمكن من الاتصال بالخادم الرئيسي حالياً. يمكنك تفعيل وضع التجربة (Mock Mode) لاختبار الواجهة."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = () => {
    if (!activeId) return;
    setConversations((prev) =>
      prev.map((c) => (c.id === activeId ? { ...c, messages: [] } : c))
    );
    setError(null);
  };

  return (
    <div className="flex h-screen max-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans overflow-hidden transition-colors duration-300">
      {/* Sidebar Component */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        conversations={conversations}
        activeId={activeId}
        onSelect={handleSelectConversation}
        onNewChat={handleNewChat}
        onDelete={handleDeleteConversation}
        onRename={handleRenameConversation}
        user={user}
        onOpenUserModal={() => setIsUserModalOpen(true)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Navigation Header */}
        <Header
          onClear={handleClear}
          hasMessages={messages.length > 0}
          isMockMode={isMockMode}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />

        {/* Chat Scroll Area */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSelectSuggestion={handleSend}
        />

        {/* Error Alert Banner */}
        {error && (
          <div className="px-4 py-2 bg-red-50 dark:bg-red-950/40 border-t border-b border-red-200/80 dark:border-red-800/80 shrink-0">
            <div className="max-w-3xl mx-auto flex items-center justify-between text-xs text-red-700 dark:text-red-300 gap-2">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600 dark:text-red-400" />
                <span>{error}</span>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-red-500 hover:text-red-800 dark:hover:text-red-200 font-bold px-1"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Floating Input Area */}
        <TextInput onSend={handleSend} disabled={isLoading} />
      </div>

      {/* User Settings Modal */}
      <UserModal
        isOpen={isUserModalOpen}
        onClose={() => setIsUserModalOpen(false)}
        user={user}
        onSave={(updated) => setUser(updated)}
      />
    </div>
  );
}