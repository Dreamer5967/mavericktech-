import React, { useEffect } from 'react';
import { ExperienceNav } from './components/ExperienceNav';
import { HeroSection } from './components/HeroSection';
import { EditorialSections } from './components/EditorialSections';

export const ExperiencePage: React.FC = () => {
  // Ensure the underlying body background matches the cinematic theme while mounted
  useEffect(() => {
    const prevBg = document.body.style.backgroundColor;
    document.body.style.backgroundColor = '#080D10';
    return () => {
      document.body.style.backgroundColor = prevBg;
    };
  }, []);

  const handleScrollToSection = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#080D10] text-white selection:bg-[#45C982] selection:text-[#080D10] font-sans">
      {/* Top Experience Navigation */}
      <ExperienceNav onSectionClick={handleScrollToSection} />

      {/* Main Experience Flow */}
      <main className="relative">
        {/* Phase 1 Opening Hero with GSAP ScrollTrigger Architecture */}
        <HeroSection />

        {/* Phase 1 Editorial Foundation (Approach, Intelligence, Digital Twin, Impact, Team) */}
        <EditorialSections />
      </main>
    </div>
  );
};

export default ExperiencePage;
