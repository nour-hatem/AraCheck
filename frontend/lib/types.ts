export type MessageRole = "user" | "assistant";

export interface Citation {
  id: number;
  pubmedId: string;
  title: string;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  citations?: Citation[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
}

export interface UserProfile {
  name: string;
  email: string;
  role: string;
  avatar?: string;
}