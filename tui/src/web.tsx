import React from 'react';
import { createRoot } from 'react-dom/client';
import Tube2TxtShowcase from './components/Tube2TxtShowcase';

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<Tube2TxtShowcase />);
}
