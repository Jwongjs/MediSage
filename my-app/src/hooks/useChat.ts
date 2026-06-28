import { useState, useCallback } from 'react';
import { ApiService, PrivacyPolicyRequiredError } from 'services/api';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: string[];
}

interface ChatHookState {
    messages: ChatMessage[];
    loading: boolean;
    error: string | null;
    privacyPolicyPending: (() => Promise<void>) | null;
}

export const useChat = () => {
    const [state, setState] = useState<ChatHookState>({
        messages: [], loading: false, error: null, privacyPolicyPending: null,
    });

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
            if (err instanceof PrivacyPolicyRequiredError) {
                // Roll back the optimistic user message; the consent modal will gate
                // the first send and re-issue it after the user accepts.
                setState(prev => ({
                    ...prev,
                    loading: false,
                    messages: prev.messages.slice(0, -1),
                    privacyPolicyPending: async () => {
                        setState(p => ({ ...p, privacyPolicyPending: null }));
                        await sendMessage(query);
                    },
                }));
                return;
            }
            setState(prev => ({
                ...prev,
                loading: false,
                error: err instanceof Error ? err.message : 'Chat failed',
            }));
        }
    }, [state.messages]);

    const handlePrivacyAccepted = useCallback(async () => {
        await ApiService.acceptPrivacyPolicy();
        if (state.privacyPolicyPending) {
            await state.privacyPolicyPending();
        }
    }, [state.privacyPolicyPending]);

    const dismissPrivacyModal = useCallback(() => {
        setState(prev => ({ ...prev, privacyPolicyPending: null }));
    }, []);

    const clearChat = useCallback(() => {
        setState({ messages: [], loading: false, error: null, privacyPolicyPending: null });
    }, []);

    return {
        messages: state.messages,
        loading: state.loading,
        error: state.error,
        showPrivacyModal: !!state.privacyPolicyPending,
        handlePrivacyAccepted,
        dismissPrivacyModal,
        sendMessage,
        clearChat,
    };
};
