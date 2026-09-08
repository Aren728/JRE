'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Stars, ChevronRight } from 'lucide-react';

const navLinks = [
  { href: '/', label: 'Home', icon: '✦' },
  { href: '/evaluate', label: 'Evaluate' },
  { href: '/evaluate/fixture', label: 'Fixtures' },
  { href: '/case-studies', label: 'Case Studies' },
  { href: '/feedback', label: 'Feedback' },
];

export default function Header() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <header
      className="sticky top-0 z-50 border-b border-white/5"
      style={{
        background: 'rgba(10, 6, 24, 0.85)',
        backdropFilter: 'blur(20px) saturate(1.3)',
        WebkitBackdropFilter: 'blur(20px) saturate(1.3)',
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, rgba(201,160,255,0.2), rgba(212,168,83,0.2))',
                border: '1px solid rgba(201,160,255,0.25)',
              }}
            >
              <Stars size={18} style={{ color: 'var(--cosmic-gold)' }} />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight" style={{ color: 'var(--cosmic-gold-light)' }}>
                JRE
              </span>
              <span className="text-[10px] hidden sm:block" style={{ color: 'var(--text-secondary)', letterSpacing: '0.05em' }}>
                JYOTISH REASONING ENGINE
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const active = isActive(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="relative px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200"
                  style={{
                    color: active ? 'var(--cosmic-gold-light)' : 'var(--text-secondary)',
                    background: active ? 'rgba(201, 160, 255, 0.1)' : 'transparent',
                    border: active ? '1px solid rgba(201, 160, 255, 0.15)' : '1px solid transparent',
                  }}
                >
                  {link.icon && <span className="mr-1">{link.icon}</span>}
                  {link.label}
                  {active && (
                    <div
                      className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 rounded-full"
                      style={{ background: 'var(--cosmic-gold)' }}
                    />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Mobile nav hint */}
          <div className="md:hidden flex items-center gap-2">
            <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>Navigate</span>
            <ChevronRight size={14} style={{ color: 'var(--text-secondary)' }} />
          </div>
        </div>
      </div>
    </header>
  );
}
