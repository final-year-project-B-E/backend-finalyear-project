import { useState } from 'react';
import { MessageCircle, Send, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface Msg { role: 'user' | 'assistant'; content: string }

export const ChatbotWidget = () => {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Msg[]>([{ role: 'assistant', content: 'Hi! I can help with products, stock, offers, support, checkout, and order tracking.' }]);

  const send = async () => {
    if (!text.trim()) return;
    const outgoing = text;
    setText('');
    setMessages((prev) => [...prev, { role: 'user', content: outgoing }]);
    try {
      const res = await api.chat({ message: outgoing, user_id: user?.id, session_id: sessionId, channel: 'web' });
      if (res.session_id) setSessionId(res.session_id);
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, chat is temporarily unavailable.' }]);
    }
  };

  return (
    <div className="fixed bottom-20 right-4 z-50">
      {open ? (
        <div className="w-[340px] h-[460px] bg-background border rounded-lg shadow-xl flex flex-col">
          <div className="p-3 border-b flex items-center justify-between"><h4 className="font-semibold">ABFRL Assistant</h4><Button variant="ghost" size="icon" onClick={() => setOpen(false)}><X className="h-4 w-4"/></Button></div>
          <ScrollArea className="flex-1 p-3 space-y-2">
            <div className="space-y-2">
              {messages.map((m, i) => (
                <div key={i} className={`p-2 rounded-md text-sm ${m.role === 'user' ? 'bg-primary text-primary-foreground ml-8' : 'bg-secondary mr-8'}`}>{m.content}</div>
              ))}
            </div>
          </ScrollArea>
          <div className="p-3 border-t flex gap-2">
            <Input value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask me anything..." onKeyDown={(e) => e.key === 'Enter' && void send()} />
            <Button onClick={() => void send()} size="icon"><Send className="h-4 w-4"/></Button>
          </div>
        </div>
      ) : (
        <Button size="icon" className="h-12 w-12 rounded-full shadow-lg" onClick={() => setOpen(true)}><MessageCircle className="h-5 w-5"/></Button>
      )}
    </div>
  );
};
