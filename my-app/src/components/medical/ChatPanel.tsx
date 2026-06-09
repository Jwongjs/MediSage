import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { useChat } from 'hooks/useChat';

const Panel = styled.div`
  display: flex;
  flex-direction: column;
  height: 500px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
`;

const Header = styled.div`
  padding: 12px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 600;
  font-size: 14px;
`;

const Messages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const Bubble = styled.div<{ role: string }>`
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  align-self: ${p => p.role === 'user' ? 'flex-end' : 'flex-start'};
  background: ${p => p.role === 'user' ? '#0070f3' : '#f0f0f0'};
  color: ${p => p.role === 'user' ? '#fff' : '#333'};
`;

const Sources = styled.div`
  font-size: 11px;
  color: #888;
  margin-top: 4px;
`;

const InputRow = styled.div`
  display: flex;
  padding: 12px;
  border-top: 1px solid #e0e0e0;
  gap: 8px;
`;

const ChatInput = styled.input`
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
`;

const SendBtn = styled.button`
  padding: 8px 16px;
  background: #0070f3;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

export const ChatPanel: React.FC = () => {
  const { messages, loading, sendMessage } = useChat();
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput('');
    await sendMessage(q);
  };

  return (
    <Panel>
      <Header>Medical History Assistant</Header>
      <Messages>
        {messages.length === 0 && (
          <Bubble role="assistant">
            Ask me anything about your past diagnoses and medical reports.
          </Bubble>
        )}
        {messages.map((m, i) => (
          <div key={i}>
            <Bubble role={m.role}>{m.content}</Bubble>
            {m.sources && m.sources.length > 0 && (
              <Sources>Sources: {m.sources.join(' | ')}</Sources>
            )}
          </div>
        ))}
        {loading && <Bubble role="assistant">Searching your records...</Bubble>}
        <div ref={bottomRef} />
      </Messages>
      <InputRow>
        <ChatInput
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your medical history..."
        />
        <SendBtn onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </SendBtn>
      </InputRow>
    </Panel>
  );
};
