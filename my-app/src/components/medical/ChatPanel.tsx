import React, { useState, useRef, useEffect } from 'react';
import { useChat } from 'hooks/useChat';
import { useAuth } from 'contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Send, Loader2, Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';

export const ChatPanel: React.FC = () => {
  const { messages, sendMessage, loading } = useChat();
  const { loggedIn } = useAuth();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput('');
    await sendMessage(q);
  };

  return (
    <div className="flex flex-col h-full border rounded-xl overflow-hidden bg-card shadow-sm">
      <div className="flex items-center gap-2.5 px-4 py-3 border-b bg-secondary/30 shrink-0">
        <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center shrink-0">
          <Bot className="h-4 w-4 text-primary" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold leading-tight">MediSage Assistant</p>
          <p className="text-xs text-muted-foreground truncate">Answers questions about your health history</p>
        </div>
        <Badge variant="outline" className="ml-auto text-xs shrink-0">Beta</Badge>
      </div>

      <ScrollArea className="flex-1 px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[200px] gap-2 text-center py-12">
            <Bot className="h-10 w-10 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">Ask me about your past diagnostic sessions or health history.</p>
            <p className="text-xs text-muted-foreground/60">I can only answer based on information from your saved reports.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, i) => {
              const isUser = msg.role === 'user';
              return (
                <div key={i} className={cn('flex items-end gap-2', isUser && 'flex-row-reverse')}>
                  <div className={cn('w-6 h-6 rounded-full flex items-center justify-center shrink-0',
                    isUser ? 'bg-primary/10' : 'bg-secondary')}>
                    {isUser ? <User className="h-3.5 w-3.5 text-primary" /> : <Bot className="h-3.5 w-3.5 text-muted-foreground" />}
                  </div>
                  <div className={cn(
                    'max-w-[80%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed',
                    isUser
                      ? 'bg-primary text-primary-foreground rounded-br-sm animate-slide-in-right'
                      : 'bg-secondary text-foreground rounded-bl-sm animate-slide-in-left',
                  )}>
                    {msg.content}
                  </div>
                </div>
              );
            })}
            {loading && (
              <div className="flex items-end gap-2">
                <div className="w-6 h-6 rounded-full bg-secondary flex items-center justify-center shrink-0">
                  <Bot className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <div className="bg-secondary rounded-2xl rounded-bl-sm px-3.5 py-3">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      <Separator />

      <form onSubmit={handleSend} className="flex items-center gap-2 px-3 py-2.5 shrink-0">
        {loggedIn ? (
          <>
            <Input value={input} onChange={e => setInput(e.target.value)}
              placeholder="Ask about your health history…"
              className="flex-1 border-0 focus-visible:ring-0 bg-transparent text-sm" disabled={loading} />
            <Button type="submit" size="icon" variant="ghost" disabled={loading || !input.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4 text-primary" />}
            </Button>
          </>
        ) : (
          <p className="text-xs text-muted-foreground py-1 w-full text-center">Sign in to use the chat assistant</p>
        )}
      </form>
    </div>
  );
};
