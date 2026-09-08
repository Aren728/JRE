'use client';

import { useEffect, useState, useMemo } from 'react';

interface Star {
  id: number;
  x: number;
  y: number;
  size: number;
  opacity: number;
  delay: number;
  duration: number;
}

function generateStars(count: number): Star[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 2.5 + 0.5,
    opacity: Math.random() * 0.7 + 0.3,
    delay: Math.random() * 5,
    duration: Math.random() * 3 + 2,
  }));
}

export default function Starfield({ starCount = 120 }: { starCount?: number }) {
  const [mounted, setMounted] = useState(false);
  const stars = useMemo(() => generateStars(starCount), [starCount]);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      {stars.map((star) => (
        <div
          key={star.id}
          style={{
            position: 'absolute',
            left: `${star.x}%`,
            top: `${star.y}%`,
            width: `${star.size}px`,
            height: `${star.size}px`,
            borderRadius: '50%',
            background: `radial-gradient(circle, rgba(255,255,255,${star.opacity}) 0%, rgba(201,160,255,${star.opacity * 0.3}) 60%, transparent 100%)`,
            animation: `twinkle ${star.duration}s ease-in-out ${star.delay}s infinite`,
            boxShadow: star.size > 1.5
              ? `0 0 ${star.size * 3}px rgba(201, 160, 255, 0.3)`
              : 'none',
          }}
        />
      ))}

      {/* Nebula patches */}
      <div
        className="absolute rounded-full blur-3xl"
        style={{
          width: '400px',
          height: '400px',
          left: '10%',
          top: '20%',
          background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute rounded-full blur-3xl"
        style={{
          width: '500px',
          height: '500px',
          right: '5%',
          top: '60%',
          background: 'radial-gradient(circle, rgba(59,130,246,0.05) 0%, transparent 70%)',
        }}
      />
    </div>
  );
}
