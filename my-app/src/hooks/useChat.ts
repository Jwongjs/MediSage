import { useState, useCallback } from 'react';
import { ApiService } from 'services/api';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
}

interface ChatHookState {
    messages: ChatMessage[];
    loading: boolean;
    error: string | null;
}

export const useChat = () => {
    const [state, setState] = useState<ChatHookState>({ messages: [], loading: false, error: null });

    const sendMessage = useCallback(async (query: string) => {
        const userMessage: ChatMessage = { role: 'user', content: query };
        setState(prev => ({
            ...prev,
            loading: true,
            error: null,
            messages: [...prev.messages, userMessage],
        }));

        const history = state.messages.map(m => ({ role: m.role, content: m.content }));
        try {
            const { answer, sources } = await ApiService.askChat(query, history);
            setState(prev => ({
                ...prev,
                loading: false,
                messages: [...prev.messages, { role: 'assistant', content: answer, sources }],
            }));
        } catch (err) {
            setState(prev => ({
                ...prev,
                loading: false,
                error: err instanceof Error ? err.message : 'Chat failed',
            }));
        }
    }, [state.messages]);

    const clearChat = useCallback(() => {
        setState({ messages: [], loading: false, error: null });
    }, []);

    return {
        messages: state.messages,
        loading: state.loading,
        error: state.error,
        sendMessage,
        clearChat,
    };
};
