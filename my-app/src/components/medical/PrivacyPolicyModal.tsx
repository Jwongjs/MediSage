import React from 'react';
import styled from 'styled-components';

interface PrivacyPolicyModalProps {
  onAccept: () => Promise<void>;
  onCancel: () => void;
}

const Overlay = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const Modal = styled.div`
  background: var(--background, #1a1a2e);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 2rem;
  max-width: 480px;
  width: 90%;
`;

const Title = styled.h2`
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-primary, #ffffff);
`;

const Body = styled.p`
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-secondary, rgba(255, 255, 255, 0.7));
  margin-bottom: 1.5rem;
`;

const ButtonRow = styled.div`
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
`;

const CancelButton = styled.button`
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  color: var(--text-secondary, rgba(255, 255, 255, 0.7));
  cursor: pointer;
  font-size: 0.9rem;
  &:hover { background: rgba(255, 255, 255, 0.05); }
`;

const AcceptButton = styled.button`
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  border: none;
  background: var(--primary, #6c63ff);
  color: #ffffff;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  &:hover { opacity: 0.9; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;

export const PrivacyPolicyModal: React.FC<PrivacyPolicyModalProps> = ({ onAccept, onCancel }) => {
  const [accepting, setAccepting] = React.useState(false);

  const handleAccept = async () => {
    setAccepting(true);
    try {
      await onAccept();
    } finally {
      setAccepting(false);
    }
  };

  return (
    <Overlay>
      <Modal>
        <Title>Data Privacy Notice</Title>
        <Body>
          Your symptom descriptions will be processed by Groq AI infrastructure to generate
          medical guidance. This service is for informational purposes only and does not
          replace professional medical advice.
          <br /><br />
          Do not enter personally identifying information (name, ID numbers, contact details)
          in symptom fields. By continuing you accept our Privacy Policy.
        </Body>
        <ButtonRow>
          <CancelButton onClick={onCancel}>Cancel</CancelButton>
          <AcceptButton onClick={handleAccept} disabled={accepting}>
            {accepting ? 'Saving...' : 'Accept & Continue'}
          </AcceptButton>
        </ButtonRow>
      </Modal>
    </Overlay>
  );
};
