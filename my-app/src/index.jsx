import React from 'react';
import ReactDOM from 'react-dom/client';

//organized CSS files
import './styles/variables.css';  // CSS custom properties first
import './styles/globals.css';    // Global styles second

import App from './App';
import reportWebVitals from './reportWebVitals';

//AuthProvider and BrowserRouter
import { AuthProvider } from 'contexts/AuthContext';
import { BrowserRouter } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async'; 


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);

reportWebVitals();