export interface Message {
  role: 'user' | 'assistant';
  content: string;
  source?: 'llm' | 'rag' | 'web';
  citations?: { id: string; url?: string; title?: string }[];
}

export class ChatContextManager {
  private history: Message[] = [];

  addMessage(message: Message) {
    this.history.push(message);
  }

  getHistory(): Message[] {
    return this.history;
  }

  clearHistory() {
    this.history = [];
  }
}

export const chatContext = new ChatContextManager();
