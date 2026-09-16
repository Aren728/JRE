'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import { Stars, Globe, User, Menu, X, ChevronDown } from 'lucide-react';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'ml', label: 'മലയാളം' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'mr', label: 'मराठी' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'as', label: 'অসমীয়া' },
  { code: 'or', label: 'ଓଡ଼ିଆ' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ' },
  { code: 'gu', label: 'ગુજરાતી' },
];

const navLinks = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/evaluate', label: 'Evaluate' },
  { href: '/chart', label: 'Charts' },
  { href: '/panchang', label: 'Panchang' },
  { href: '/compatibility', label: 'Compatibility' },
];

export default function Navbar() {
  const pathname = usePathname();
  const [lang, setLang] = useState('en');
  const [langOpen, setLangOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const langRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (langRef.current && !langRef.current.contains(e.target as Node)) {
        setLangOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const isActive = (href: string) => {
    if (href === '/dashboard') return pathname === '/dashboard' || pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <header className="navbar-glass sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-3 group shrink-0">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, rgba(197,168,128,0.25), rgba(197,168,128,0.08))',
                border: '1px solid rgba(197,168,128,0.3)',
              }}
            >
              <Stars size={18} style={{ color: 'var(--cosmic-gold)' }} />
            </div>
            <div className="flex flex-col">
              <span
                className="text-lg font-bold tracking-tight"
                style={{ color: 'var(--cosmic-gold)', fontFamily: 'var(--font-playfair), Georgia, serif' }}
              >
                JRE Cosmic
              </span>
              <span
                className="text-[10px] hidden sm:block tracking-widest uppercase"
                style={{ color: 'var(--cosmic-muted)' }}
              >
                Jyotish Reasoning Engine
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`navbar-link ${isActive(link.href) ? 'active' : ''}`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Right side: Language + Profile */}
          <div className="flex items-center gap-3">
            {/* Language Dropdown */}
            <div ref={langRef} className="relative">
              <button
                type="button"
                onClick={() => setLangOpen(!langOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200"
                style={{
                  background: 'rgba(197, 168, 128, 0.08)',
                  border: '1px solid rgba(197, 168, 128, 0.15)',
                  color: 'var(--cosmic-gold)',
                }}
                title="Select language"
              >
                <Globe size={13} />
                <span>{LANGUAGES.find((l) => l.code === lang)?.label || 'English'}</span>
                <ChevronDown size={11} className={`transition-transform ${langOpen ? 'rotate-180' : ''}`} />
              </button>
              {langOpen && (
                <div
                  className="absolute right-0 mt-1 w-40 rounded-xl py-1 z-50 max-h-64 overflow-y-auto"
                  style={{
                    background: 'rgba(26, 20, 35, 0.95)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(197, 168, 128, 0.2)',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                  }}
                >
                  {LANGUAGES.map((l) => (
                    <button
                      key={l.code}
                      type="button"
                      onClick={() => { setLang(l.code); setLangOpen(false); }}
                      className="w-full text-left px-3 py-1.5 text-xs transition-colors"
                      style={{
                        color: l.code === lang ? 'var(--cosmic-gold)' : 'var(--cosmic-muted)',
                        background: l.code === lang ? 'rgba(197,168,128,0.1)' : 'transparent',
                      }}
                    >
                      {l.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* User Profile */}
            <button
              type="button"
              className="w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200"
              style={{
                background: 'rgba(197, 168, 128, 0.08)',
                border: '1px solid rgba(197, 168, 128, 0.15)',
                color: 'var(--cosmic-muted)',
              }}
              title="User profile"
            >
              <User size={16} />
            </button>

            {/* Mobile menu toggle */}
            <button
              type="button"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden w-9 h-9 rounded-lg flex items-center justify-center"
              style={{
                background: 'rgba(197, 168, 128, 0.08)',
                border: '1px solid rgba(197, 168, 128, 0.15)',
                color: 'var(--cosmic-muted)',
              }}
            >
              {mobileOpen ? <X size={16} /> : <Menu size={16} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown */}
        {mobileOpen && (
          <div className="md:hidden pb-4 border-t border-white/5 mt-2 pt-3">
            <nav className="flex flex-col gap-1">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`navbar-link ${isActive(link.href) ? 'active' : ''}`}
                >
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
