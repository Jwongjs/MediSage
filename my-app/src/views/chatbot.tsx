import React, { useState } from 'react';
import styled from 'styled-components';
import Navbar from 'components/homepage/Navbar';
import { Button } from 'components/common/Button';
import { Input } from 'components/common/Input';
import { Card } from 'components/common/Card';
import { useAuth } from 'contexts/AuthContext';

const ChatbotWrapper = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
`;

const ChatbotHeader = styled.div`
  text-align: center;
  margin-bottom: 2rem;
  
  h1 {
    margin: 0 0 0.5rem 0;
    color: var(--dark);
    font-size: 2rem;
  }
  
  p {
    margin: 0;
    color: var(--secondary);
    font-size: 1rem;
  }
`;

const ChatContainer = styled(Card)`
  height: 500px;
  display: flex;
  flex-direction: column;
  padding: 0;
`;

const ChatMessages = styled.div`
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  border-bottom: 1px solid #e9ecef;
`;

const ChatInput = styled.div`
  padding: 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
`;

const Message = styled.div<{ isUser: boolean }>`
  margin-bottom: 1rem;
  display: flex;
  justify-content: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  
  .message-content {
    max-width: 70%;
    padding: 0.75rem 1rem;
    border-radius: 1rem;
    background: ${props => props.isUser ? 'var(--primary)' : '#f8f9fa'};
    color: ${props => props.isUser ? 'white' : 'var(--dark)'};
  }
`;

const PlaceholderMessage = styled.div`
  text-align: center;
  color: var(--secondary);
  font-style: italic;
  margin-top: 2rem;
`;

const ChatbotPage: React.FC = () => {
  const { loggedIn } = useAuth();
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean; timestamp: Date }>>([
    {
      text: "Hello! I'm your medical assistant. How can I help you today?",
      isUser: false,
      timestamp: new Date()
    }
  ]);

  const handleSendMessage = () => {
    if (!message.trim()) return;

    // Add user message
    const newUserMessage = {
      text: message,
      isUser: true,
      timestamp: new Date()
    };

    // Add bot response (placeholder)
    const botResponse = {
      text: "Thank you for your message. The chatbot functionality is currently under development. For now, please use the diagnosis tool for medical analysis.",
      isUser: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage, botResponse]);
    setMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!loggedIn) {
    return (
      <>
        <Navbar loggedIn={false} />
        <ChatbotWrapper>
          <Card>
            <div style={{ textAlign: 'center', padding: '2rem' }}>
              <h2>🔒 Login Required</h2>
              <p>Please log in to access the medical chatbot.</p>
              <Button 
                variant="primary" 
                onClick={() => window.location.href = '/login'}
                style={{ marginTop: '1rem' }}
              >
                Go to Login
              </Button>
            </div>
          </Card>
        </ChatbotWrapper>
      </>
    );
  }

  return (
    <>
      <Navbar loggedIn={loggedIn} />
      <ChatbotWrapper>
        <ChatbotHeader>
          <h1>🤖 Medical Chatbot</h1>
          <p>Ask questions about your health and get AI-powered assistance</p>
        </ChatbotHeader>

        <ChatContainer>
          <ChatMessages>
            {messages.map((msg, index) => (
              <Message key={index} isUser={msg.isUser}>
                <div className="message-content">
                  {msg.text}
                </div>
              </Message>
            ))}
            <PlaceholderMessage>
              💡 This chatbot is currently under development. For medical diagnosis, please use the "Start Diagnosis" feature.
            </PlaceholderMessage>
          </ChatMessages>

          <ChatInput>
            <Input
              type="textarea"
              value={message}
              onChange={setMessage}
              placeholder="Type your medical question here..."
              onKeyDown={handleKeyPress}
              style={{ flex: 1 }}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!message.trim()}
              variant="primary"
            >
              Send
            </Button>
          </ChatInput>
        </ChatContainer>

        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <Button
            variant="secondary"
            onClick={() => window.location.href = '/diagnosis'}
          >
            🩺 Switch to Full Diagnosis Tool
          </Button>
        </div>
      </ChatbotWrapper>
    </>
  );
};

export default ChatbotPage;