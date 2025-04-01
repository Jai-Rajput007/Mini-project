"use client";
import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ColourfulText from "@/components/ui/colourful-text";
import PhishingCards from "@/components/PhishingCards";
import LinkCheckerForm from "@/components/LinkCheckerForm";
import { TypingAnimation } from "@/components/magicui/typing-animation";
import dynamic from "next/dynamic";
import { AnimatedTestimonials } from "@/components/ui/animated-testimonials";

// Create a client-only version of the typing animation section
const ClientOnlyTypingSection = dynamic(
  () => Promise.resolve(({ questionText, cursorStyle }: { questionText: string; cursorStyle: string }) => {
    const [animationKey, setAnimationKey] = useState(0);
    
    // Simple animation cycle with fixed timing
    useEffect(() => {
      // Set up a repeating cycle for the animation
      const animationCycle = () => {
        // Increment the key to restart the animation
        setAnimationKey(prev => prev + 1);
        
        // Schedule the next cycle
        setTimeout(animationCycle, 12000); // Total cycle time: ~7s typing + 5s pause
      };
      
      // Start the first cycle after a short delay
      const initialTimer = setTimeout(animationCycle, 12000);
      
      return () => {
        clearTimeout(initialTimer);
      };
    }, []);
    
    return (
      <div className="text-center relative">
        <div className="inline-flex items-center">
          {/* Simple key-based animation restart */}
          <TypingAnimation
            key={animationKey}
            className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white leading-normal"
            duration={150} // Typing speed
            delay={100} // Initial delay
          >
            {questionText}
          </TypingAnimation>
          
          {/* Blinking cursor */}
          <span 
            className="inline-block text-3xl md:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white ml-1"
            style={{ 
              animation: 'blink 1s step-end infinite',
              position: 'relative',
              top: cursorStyle === 'underscore' ? '0.1em' : '0'
            }}
          >
            {cursorStyle === 'pipe' ? '|' : '_'}
          </span>
        </div>
      </div>
    );
  }),
  { ssr: false }
);

// Recent major phishing attacks data
const recentAttacks = [
  {
    quote: "A sophisticated phishing campaign targeting Microsoft 365 users, employing OAuth consent phishing to gain persistent access to victims' email accounts and data.",
    name: "Microsoft 365 OAuth Attack",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80"
  },
  {
    quote: "Attackers impersonated ChatGPT to distribute info-stealing malware through fake browser extensions and websites.",
    name: "ChatGPT Impersonation Attack",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80"
  },
  {
    quote: "A large-scale phishing operation using fake QR codes to steal cryptocurrency wallet credentials and digital assets.",
    name: "Crypto QR Code Scam",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1563986768609-322da13575f3?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80"
  },
  {
    quote: "Sophisticated attack targeting banking customers through SMS phishing (smishing) with fake bank security alerts.",
    name: "Banking SMS Phishing",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1618044733300-9472054094ee?ixlib=rb-4.0.3&auto=format&fit=crop&w=1471&q=80"
  },
  {
    quote: "Major phishing campaign exploiting Google Docs comments to distribute malicious links to corporate users.",
    name: "Google Docs Comment Exploit",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1573164713988-8665fc963095?ixlib=rb-4.0.3&auto=format&fit=crop&w=1469&q=80"
  },
  {
    quote: "Large-scale business email compromise attack targeting corporate executives through fake Microsoft Teams notifications.",
    name: "Teams Notification Attack",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1562577309-4932fdd64cd1?ixlib=rb-4.0.3&auto=format&fit=crop&w=1474&q=80"
  },
  {
    quote: "Advanced phishing campaign using AI-generated voice cloning to conduct vishing (voice phishing) attacks on employees.",
    name: "AI Voice Cloning Scam",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80"
  },
  {
    quote: "Sophisticated attack using fake cloud storage notifications to harvest corporate credentials and sensitive data.",
    name: "Cloud Storage Credential Theft",
    designation: "", // Keep empty as requested
    src: "https://images.unsplash.com/photo-1510511459019-5dda7724fd87?ixlib=rb-4.0.3&auto=format&fit=crop&w=1470&q=80"
  }
];

export default function PhishingPage() {
  // Simplified state management
  const questionText = "Why should you be concerned about Phishing ?";
  
  // Choose cursor style: 'pipe' for | or 'underscore' for _
  const cursorStyle = 'pipe'; // Change to 'underscore' if you prefer _ cursor
  
  return (
    <div className="min-h-screen w-full flex flex-col items-center relative overflow-hidden bg-white dark:bg-black">
      <motion.h1 
        className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-center text-gray-800 dark:text-white relative z-2 font-sans px-4 mt-36"
        initial={{ opacity: 0, y: -20 }}
        animate={{ 
          opacity: 1, 
          y: 0,
          transition: {
            duration: 0.8,
            ease: "easeOut",
            delay: 0.3
          }
        }}
      >
        Annoyed with <ColourfulText text="fake" theme="red" /> or <ColourfulText text="phishing" theme="red" /> sites?
      </motion.h1>

      {/* Process Cards */}
      <PhishingCards />
      
      {/* Link Checker Form */}
      <LinkCheckerForm />
      
      {/* Separator line with "Learn More" label */}
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-16">
        <div className="relative flex items-center">
          <div className="flex-grow border-t border-gray-300 dark:border-gray-700 opacity-50"></div>
          <span className="flex-shrink mx-4 text-lg font-medium text-gray-500 dark:text-gray-400">Learn More</span>
          <div className="flex-grow border-t border-gray-300 dark:border-gray-700 opacity-50"></div>
        </div>
      </div>
      
      {/* Typing Animation Section with professional spacing */}
      <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-16 mb-8">
        <div className="flex justify-center min-h-[150px] items-center">
          <ClientOnlyTypingSection questionText={questionText} cursorStyle={cursorStyle} />
        </div>
        
        {/* Recent Attacks Section - Using AnimatedTestimonials */}
        <div className="w-full mx-auto mt-24 mb-32">
          <div className="relative">
            <AnimatedTestimonials 
              testimonials={recentAttacks} 
              autoplay={false} 
            />
            {/* Add custom styles to override shadcn defaults */}
            <style dangerouslySetInnerHTML={{ __html: `
              /* Fix text colors */
              .dark .text-black {
                color: hsl(var(--foreground)) !important;
              }
              .text-black {
                color: hsl(var(--foreground)) !important;
              }
              
              /* Fix neutral colors */
              .text-gray-500, .text-neutral-500 {
                color: hsl(var(--muted-foreground)) !important;
              }
              .dark .text-gray-500, .dark .text-neutral-500 {
                color: hsl(var(--muted-foreground)) !important;
              }
              
              /* Fix background colors */
              .bg-gray-100, .bg-neutral-100 {
                background-color: hsl(var(--muted)) !important;
              }
              .dark .bg-gray-100, .dark .bg-neutral-100 {
                background-color: hsl(var(--muted)) !important;
              }
              
              /* Fix button colors */
              .text-neutral-600 {
                color: hsl(var(--foreground)) !important;
              }
              .dark .text-neutral-600 {
                color: hsl(var(--foreground)) !important;
              }
              
              /* Fix button backgrounds */
              .bg-neutral-200, .bg-gray-200 {
                background-color: hsl(var(--accent)) !important;
              }
              .dark .bg-neutral-200, .dark .bg-gray-200 {
                background-color: hsl(var(--accent)) !important;
              }
              
              /* Fix testimonial text */
              .text-neutral-300, .text-gray-300 {
                color: hsl(var(--muted-foreground)) !important;
              }
              .dark .text-neutral-300, .dark .text-gray-300 {
                color: hsl(var(--muted-foreground)) !important;
              }
              
              /* Fix image borders */
              .rounded-3xl {
                border-radius: var(--radius) !important;
              }
              
              /* Fix button hover states */
              .group-hover\\/button\\:-rotate-12, .group-hover\\/button\\:rotate-12 {
                color: hsl(var(--accent-foreground)) !important;
              }
              
              /* Fix animation colors */
              .text-gray-500 span {
                color: hsl(var(--muted-foreground)) !important;
              }
              
              /* Fix rounded corners */
              .rounded-full {
                border-radius: 9999px !important;
              }
              
              /* Fix button backgrounds */
              .bg-gray-100, .dark .bg-neutral-800 {
                background-color: hsl(var(--accent)) !important;
              }
            ` }} />
          </div>
          <div className="text-center mt-24 max-w-2xl mx-auto">
            <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
              These recent attacks demonstrate the evolving sophistication of phishing threats. 
              Stay protected by using our link checker tool to verify suspicious links before clicking.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 