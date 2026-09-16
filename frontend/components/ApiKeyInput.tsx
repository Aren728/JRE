'use client';

import { useEffect, useState } from 'react';
import { Key, Eye, EyeOff } from 'lucide-react';

interface ApiKeyInputProps {
  value: string;
  onChange: (value: string) => void;
}

export default function ApiKeyInput({ value, onChange }: ApiKeyInputProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div>
      <label className="cosmic-label">
        <Key size={12} className="inline mr-1" />
        API Key
      </label>
      <div className="relative">
        <input
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="jre-beta-key-alpha"
          className="cosmic-input pr-10 font-mono text-sm"
        />
        <button
          type="button"
          onClick={() => setVisible(!visible)}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded transition-colors"
          style={{ color: 'var(--text-secondary)' }}
          title={visible ? 'Hide key' : 'Show key'}
        >
          {visible ? <EyeOff size={14} /> : <Eye size={14} />}
        </button>
      </div>
      <p className="text-[11px] mt-1.5" style={{ color: 'var(--text-secondary)', opacity: 0.6 }}>
        Stored in your browser localStorage. Never sent to third parties.
      </p>
    </div>
  );
}

export function useApiKey() {
  const [apiKey, setApiKey] = useState('jre-beta-key-alpha');

  useEffect(() => {
    const stored = localStorage.getItem('jre_api_key');
    if (stored) setApiKey(stored);
    else localStorage.setItem('jre_api_key', 'jre-beta-key-alpha');
  }, []);

  const updateApiKey = (key: string) => {
    setApiKey(key);
    localStorage.setItem('jre_api_key', key);
  };

  return { apiKey, setApiKey: updateApiKey };
}
