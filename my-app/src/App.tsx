import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Homepage  from 'views/homepage';
import DiagnosisFunction from 'views/diagnosis';
import PrivacyPolicyPage from 'views/privacypolicy';
import TermsPage from 'views/terms';

function App(): React.JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<Homepage />} />
      <Route path="/diagnosis" element={<DiagnosisFunction />} />
      <Route path="/privacy" element={<PrivacyPolicyPage />} />
      <Route path="/terms" element={<TermsPage />} />
    </Routes>
  );
}

export default App;