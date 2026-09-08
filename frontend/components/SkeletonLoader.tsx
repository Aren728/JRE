'use client';

import React from 'react';

export const SkeletonLoader: React.FC = () => {
  return (
    <div className="space-y-6 animate-pulse" data-testid="skeleton-loader">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="h-28 bg-gray-200 rounded-lg" />
        <div className="h-28 bg-gray-200 rounded-lg" />
      </div>
      <div className="h-64 bg-gray-200 rounded-lg" />
      <div className="h-96 bg-gray-200 rounded-lg" />
    </div>
  );
};
