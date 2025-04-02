import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import React from 'react';
import Form from './Form'; // make sure path is correct

function App() {
  const [count, setCount] = useState(0)

  return (
    <div>
      <h1>Test AI Agent Locally</h1>
      <Form />
    </div>
  );
}

export default App
