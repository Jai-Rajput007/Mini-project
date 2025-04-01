"use client";
import { title } from "@/components/primitives";
import { Feature } from "@/components/ui/feature-with-image-comparison";
import { FeatureComparison } from "@/components/pages/about/feature-comparison";
import React, { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/dist/ScrollTrigger";

export default function AboutPage() {
  // State to track if the page has loaded
  const [isLoaded, setIsLoaded] = useState(false);

  // Register ScrollTrigger plugin
  useEffect(() => {
    if (typeof window !== "undefined") {
      gsap.registerPlugin(ScrollTrigger);
      // Set loaded state after a short delay to ensure DOM is ready
      const timer = setTimeout(() => setIsLoaded(true), 100);
      return () => clearTimeout(timer);
    }
  }, []);

  // References for sections
  const introRef = useRef<HTMLDivElement>(null);
  const howItWorksRef = useRef<HTMLDivElement>(null);
  const whyImportantRef = useRef<HTMLDivElement>(null);
  const whoWeAreRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const timelineProgressRef = useRef<HTMLDivElement>(null);

  // Set up animations
  useEffect(() => {
    if (typeof window === "undefined" || !isLoaded) return;

    // Create a timeline for each section
    const sections = [introRef, howItWorksRef, whyImportantRef, whoWeAreRef];
    
    // Clear any existing ScrollTriggers
    ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    
    // Set up the timeline progress animation
    gsap.to(timelineProgressRef.current, {
      height: "100%",
      ease: "none",
      scrollTrigger: {
        trigger: "body",
        start: "top top",
        end: "bottom bottom",
        scrub: 0.3
      }
    });

    // Animate each section
    sections.forEach((sectionRef, index) => {
      const section = sectionRef.current;
      if (!section) return;

      // Get all headings and content blocks in the section
      const headings = section.querySelectorAll('h2, h3');
      const contentBlocks = section.querySelectorAll('.content-block');
      
      // Animate headings
      gsap.fromTo(headings, 
        { opacity: 0, y: 50 },
        { 
          opacity: 1, 
          y: 0, 
          duration: 0.8,
          stagger: 0.2,
          scrollTrigger: {
            trigger: section,
            start: "top 70%",
            toggleActions: "play none none reverse"
          }
        }
      );
      
      // Animate content blocks
      gsap.fromTo(contentBlocks, 
        { opacity: 0, y: 30 },
        { 
          opacity: 1, 
          y: 0, 
          duration: 0.6,
          stagger: 0.15,
          scrollTrigger: {
            trigger: section,
            start: "top 60%",
            toggleActions: "play none none reverse"
          }
        }
      );

      // Highlight the current timeline dot
      ScrollTrigger.create({
        trigger: section,
        start: "top center",
        end: "bottom center",
        toggleClass: { targets: `#timeline-dot-${index}`, className: "active" },
        onEnter: () => {
          document.querySelectorAll('.timeline-label').forEach(el => 
            el.classList.remove('text-primary')
          );
          document.querySelector(`#timeline-label-${index}`)?.classList.add('text-primary');
        },
        onEnterBack: () => {
          document.querySelectorAll('.timeline-label').forEach(el => 
            el.classList.remove('text-primary')
          );
          document.querySelector(`#timeline-label-${index}`)?.classList.add('text-primary');
        }
      });
    });

    // Handle window resize
    const handleResize = () => {
      ScrollTrigger.refresh();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      // Clean up all ScrollTriggers when component unmounts
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
      window.removeEventListener('resize', handleResize);
    };
  }, [isLoaded]);

  return (
    <main className="min-h-screen w-full relative">
      {/* Fixed Timeline Navigation */}
      <div 
        ref={timelineRef}
        className="fixed left-4 md:left-8 top-1/2 -translate-y-1/2 h-[60vh] z-50 flex items-center"
      >
        <div className="relative h-full flex flex-col items-center">
          {/* Timeline track */}
          <div className="absolute h-full w-[2px] bg-gray-200 dark:bg-gray-700"></div>
          
          {/* Timeline progress */}
          <div 
            ref={timelineProgressRef}
            className="absolute top-0 w-[2px] h-0 bg-primary"
          ></div>
          
          {/* Timeline dots */}
          <a 
            href="#introduction" 
            id="timeline-dot-0"
            className="timeline-dot absolute top-0 w-4 h-4 rounded-full bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 -left-[7px] transition-all duration-300 hover:scale-125 z-10"
          >
            <span id="timeline-label-0" className="timeline-label absolute left-6 top-0 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-gray-600 dark:text-gray-300 transition-colors duration-300">
              Introduction
            </span>
          </a>
          
          <a 
            href="#how-it-works" 
            id="timeline-dot-1"
            className="timeline-dot absolute top-1/3 w-4 h-4 rounded-full bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 -left-[7px] transition-all duration-300 hover:scale-125 z-10"
          >
            <span id="timeline-label-1" className="timeline-label absolute left-6 top-0 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-gray-600 dark:text-gray-300 transition-colors duration-300">
              How It Works
            </span>
          </a>
          
          <a 
            href="#why-important" 
            id="timeline-dot-2"
            className="timeline-dot absolute top-2/3 w-4 h-4 rounded-full bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 -left-[7px] transition-all duration-300 hover:scale-125 z-10"
          >
            <span id="timeline-label-2" className="timeline-label absolute left-6 top-0 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-gray-600 dark:text-gray-300 transition-colors duration-300">
              Why It's Important
            </span>
          </a>
          
          <a 
            href="#who-we-are" 
            id="timeline-dot-3"
            className="timeline-dot absolute bottom-0 w-4 h-4 rounded-full bg-white dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-600 -left-[7px] transition-all duration-300 hover:scale-125 z-10"
          >
            <span id="timeline-label-3" className="timeline-label absolute left-6 top-0 -translate-y-1/2 whitespace-nowrap text-sm font-medium text-gray-600 dark:text-gray-300 transition-colors duration-300">
              Who We Are
            </span>
          </a>
        </div>
      </div>

      {/* Content Sections */}
      <div className="ml-16 md:ml-32">
        {/* Introduction Section */}
        <section 
          id="introduction" 
          ref={introRef}
          className="min-h-screen py-20 px-4 sm:px-6 lg:px-8"
        >
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 dark:text-white mb-16">
              Introduction
            </h2>
            
            {/* About Safex */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                About Safex
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Safex is a comprehensive security platform designed to protect users from various online threats, 
                  with a special focus on phishing detection and prevention. Our mission is to create a safer 
                  internet experience for everyone by providing powerful, easy-to-use tools that help identify 
                  and avoid malicious websites and scams.
                </p>
                {/* Add your content here */}
                {/* You can add more paragraphs, images, or other elements */}
              </div>
            </div>
            
            {/* Features */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Features
              </h3>
              <div className="w-full">
                <FeatureComparison />
                {/* Add your content here */}
                {/* You can add more feature descriptions, lists, or other elements */}
              </div>
            </div>
            
            {/* Tech Stack */}
            <div className="content-block">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Tech Stack
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                {/* You can add technology logos, descriptions, or other elements */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Our platform is built using cutting-edge technologies to ensure reliability, security, and performance.
                  The tech stack includes modern frameworks, machine learning algorithms, and robust security protocols.
                </p>
              </div>
            </div>
          </div>
        </section>
        
        {/* How It Works Section */}
        <section 
          id="how-it-works" 
          ref={howItWorksRef}
          className="min-h-screen py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900"
        >
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 dark:text-white mb-16">
              How It Works
            </h2>
            
            {/* Web Assessment Tool */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Web Assessment Tool
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Our web assessment tool analyzes websites in real-time to identify potential security threats.
                  It checks for common indicators of phishing attempts and provides immediate feedback to users.
                </p>
              </div>
            </div>
            
            {/* Scanning */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Scanning
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Our scanning technology examines multiple aspects of websites, including URL structure,
                  content patterns, SSL certificates, and domain reputation to determine their legitimacy.
                </p>
              </div>
            </div>
            
            {/* Checking Vulnerabilities */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Checking Vulnerabilities
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  We identify potential vulnerabilities that could be exploited by attackers,
                  helping users understand the risks associated with visiting certain websites.
                </p>
              </div>
            </div>
            
            {/* Generating Reports */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Generating Reports
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  After analysis, we generate comprehensive reports that detail any security concerns,
                  providing users with actionable information to make informed decisions.
                </p>
              </div>
            </div>
            
            {/* Phishing */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Phishing Detection
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Our specialized phishing detection algorithms can identify even sophisticated
                  phishing attempts that mimic legitimate websites with high accuracy.
                </p>
              </div>
            </div>
            
            {/* Him.ai */}
            <div className="content-block">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Him.ai Integration
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  We leverage advanced AI technology to continuously improve our detection capabilities,
                  adapting to new threats as they emerge in the digital landscape.
                </p>
              </div>
            </div>
          </div>
        </section>
        
        {/* Why It's Important Section */}
        <section 
          id="why-important" 
          ref={whyImportantRef}
          className="min-h-screen py-20 px-4 sm:px-6 lg:px-8"
        >
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 dark:text-white mb-16">
              Why It's Important
            </h2>
            
            {/* Need for This */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Need for This Solution
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  As digital threats continue to evolve, traditional security measures are often insufficient.
                  Safex fills a critical gap by providing accessible, user-friendly protection against sophisticated phishing attacks.
                </p>
              </div>
            </div>
            
            {/* Current Situation Globally */}
            <div className="content-block mb-24">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Current Situation Globally
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Phishing attacks have increased by over 300% in recent years, with billions of dollars
                  lost annually to these scams. The global impact affects individuals, businesses, and organizations of all sizes.
                </p>
              </div>
            </div>
            
            {/* Additional Points */}
            <div className="content-block">
              <h3 className="text-2xl md:text-3xl font-semibold text-gray-800 dark:text-gray-100 mb-8">
                Impact on Digital Trust
              </h3>
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Widespread phishing attacks erode trust in digital platforms and services.
                  By providing reliable protection, Safex helps restore confidence in online interactions.
                </p>
              </div>
            </div>
          </div>
        </section>
        
        {/* Who We Are Section */}
        <section 
          id="who-we-are" 
          ref={whoWeAreRef}
          className="min-h-screen py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900"
        >
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl md:text-5xl font-bold text-gray-900 dark:text-white mb-16">
              Who We Are
            </h2>
            
            <div className="content-block">
              <div className="prose dark:prose-invert max-w-3xl">
                {/* Add your content here */}
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  Safex was founded by a team of cybersecurity experts with decades of combined experience 
                  in the field. We're passionate about making the internet safer and more accessible for everyone, 
                  regardless of their technical expertise.
                </p>
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
                  Our diverse team brings together expertise in cybersecurity, machine learning, user experience design,
                  and software development to create a comprehensive solution to the growing threat of phishing attacks.
                </p>
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed mt-4">
                  We believe that everyone deserves to feel safe online, and we're committed to making that a reality
                  through innovative technology and accessible education.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Add custom styles for the timeline */}
      <style jsx>{`
        .timeline-dot.active {
          background-color: hsl(var(--primary));
          border-color: hsl(var(--primary));
          transform: scale(1.25);
        }
        
        @media (max-width: 768px) {
          .timeline-label {
            display: none;
          }
        }
      `}</style>
    </main>
  );
}
