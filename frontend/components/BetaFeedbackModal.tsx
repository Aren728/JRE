'use client';

import React, { useState } from 'react';
import { isFeatureEnabled } from '@/config/featureFlags';

export function BetaFeedbackModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!isFeatureEnabled('enableBetaFeedbackModal')) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${apiUrl}/api/v1/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: feedback,
          timestamp: new Date().toISOString(),
        }),
      });
      setSubmitted(true);
      setTimeout(() => {
        setIsOpen(false);
        setSubmitted(false);
        setFeedback('');
      }, 2000);
    } catch (err) {
      console.error('Feedback submission failed', err);
    }
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 bg-indigo-600 hover:bg-indigo-700 text-white font-medium px-4 py-2 rounded-full shadow-lg transition-all"
      >
        💬 Beta Feedback
      </button>

      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-xl max-w-md w-full shadow-2xl relative">
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">
              Share Beta Feedback
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              Help us refine calculation precision and UI performance.
            </p>

            {submitted ? (
              <div className="p-4 bg-green-100 text-green-800 rounded-lg text-center font-medium">
                Thank you! Your feedback has been recorded.
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Tell us about any discrepancies or issues..."
                  required
                  rows={4}
                  className="w-full p-3 border rounded-lg dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  type="submit"
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 rounded-lg transition-colors"
                >
                  Submit Feedback
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
