"use client";
import React, { useState, useEffect, FormEvent } from "react";
import { motion } from "framer-motion";
import { Cover } from "@/components/ui/cover";
import { cn } from "@/lib/utils";
import { HoverBorderGradient } from "@/components/ui/hover-border-gradient";
import { MultiStepLoader } from "@/components/ui/multi-step-loader";
import { BorderBeam } from "@/components/magicui/border-beam";
import { TypingAnimation } from "@/components/magicui/typing-animation";

// Define types for loading states
interface LoadingState {
  text: string;
}

// Define props for CustomCover component
interface CustomCoverProps {
  children: React.ReactNode;
  className?: string;
}

export default function LinkCheckerForm(): React.ReactElement | null {
  const [link, setLink] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);
  const [showResults, setShowResults] = useState<boolean>(false);
  const [displayText, setDisplayText] = useState<string>("");
  
  // Text to be generated character by character
  const resultsText = "Here's the Results";
  
  // Define loading states for MultiStepLoader
  const loadingStates: LoadingState[] = [
    { text: "Checking URL structure..." },
    { text: "Scanning for suspicious patterns..." },
    { text: "Verifying domain reputation..." },
    { text: "Analyzing SSL certificate..." },
    { text: "Checking for phishing indicators..." }
  ];
  
  // Only run on client-side to prevent hydration errors
  useEffect(() => {
    setMounted(true);
  }, []);
  
  // Handle text animation when results should be shown
  useEffect(() => {
    if (!showResults) {
      setDisplayText("");
      return;
    }
    
    let currentIndex = 0;
    const textInterval = setInterval(() => {
      if (currentIndex <= resultsText.length) {
        setDisplayText(resultsText.substring(0, currentIndex));
        currentIndex++;
      } else {
        clearInterval(textInterval);
      }
    }, 100);
    
    return () => clearInterval(textInterval);
  }, [showResults]);
  
  // Handle button click directly
  const handleButtonClick = () => {
    console.log("Button clicked!");
    
    // Only proceed if there's a link
    if (!link) {
      console.log("No link provided");
      return;
    }
    
    console.log("Processing link:", link);
    
    // Reset results and show loading
    setShowResults(false);
    setIsLoading(true);
    
    // Simulate processing time then show results
    setTimeout(() => {
      console.log("Loading complete, showing results");
      setIsLoading(false);
      setShowResults(true);
    }, 7000); // Reduced from 10 seconds to 7 seconds
  };

  // Custom Cover component with light theme support
  const CustomCover: React.FC<CustomCoverProps> = ({ children, className }) => {
    return (
      <div className="relative">
        <Cover className={cn("text-xl md:text-2xl px-4 py-3", className)}>
          <span className="font-semibold text-gray-800 dark:text-white hover-white">
            {children}
          </span>
        </Cover>
        {/* Add an overlay to ensure text is visible in light mode */}
        <style jsx global>{`
          /* Override Cover component styles for light theme */
          .group\/cover:hover {
            background: #1e293b !important; /* slate-800 */
          }
          .group\/cover {
            background: white !important;
            border: 1px solid #e2e8f0 !important; /* slate-200 */
          }
          .dark .group\/cover {
            background: #0f172a !important; /* slate-900 */
            border: 1px solid #334155 !important; /* slate-700 */
          }
          /* Fix text visibility on hover */
          .group-hover\/cover\:text-white {
            color: white !important;
          }
          /* Force text to be white on hover */
          .group\/cover:hover span {
            color: white !important;
          }
          /* Add a custom class for hover state */
          .hover-white:hover {
            color: white !important;
          }
          /* Ensure beam animations are visible */
          .group\/cover:hover path {
            stroke-width: 2px !important;
            opacity: 1 !important;
          }
          /* Increase sparkles visibility */
          .group\/cover:hover .opacity-0 {
            opacity: 1 !important;
          }
          /* Ensure Cover is above other elements */
          .group\/cover {
            z-index: 50 !important;
            position: relative !important;
          }
        `}</style>
      </div>
    );
  };

  // Don't render anything until mounted to prevent hydration errors
  if (!mounted) {
    return null;
  }

  return (
    <>
      <div className="w-full max-w-7xl mx-auto mt-12 mb-24 px-4 sm:px-6 lg:px-8">
        {/* Card with simple outline and BorderBeam */}
        <div className="relative max-w-5xl mx-auto pt-10">
          {/* "Give it a try" text with Cover component - Moved outside card for better visibility */}
          <div className="absolute -top-1 left-8 z-50">
            <CustomCover>
              Give it a try
            </CustomCover>
          </div>
          
          {/* Card content */}
          <div className="relative z-10 backdrop-blur-sm bg-transparent border border-gray-300 dark:border-gray-700 rounded-xl p-12 min-h-[400px] flex flex-col justify-center transition-colors duration-300 overflow-hidden">
            {/* BorderBeam animation */}
            <BorderBeam 
              size={60} 
              duration={8} 
              colorFrom="#00b7ff" 
              colorTo="#7828c8" 
              className="opacity-70"
            />
            <BorderBeam 
              size={60} 
              duration={8} 
              colorFrom="#7828c8" 
              colorTo="#00b7ff" 
              reverse={true} 
              initialOffset={50}
              className="opacity-70"
            />
            
            {/* Input form - Changed to div to avoid form submission issues */}
            <div className="w-full max-w-lg mx-auto relative z-10">
              <div className="space-y-8">
                <div className="space-y-3">
                  <label className="text-base font-medium text-gray-700 dark:text-gray-300">
                    Suspicious Link
                  </label>
                  <div className="relative">
                    <input
                      type="url"
                      value={link}
                      onChange={(e) => setLink(e.target.value)}
                      className="flex h-12 w-full rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-black px-4 py-3 text-base text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-colors duration-200"
                      placeholder="Enter the suspected Link"
                    />
                    {!link && (
                      <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                        <span className="text-gray-400 dark:text-gray-500">Enter the suspected Link</span>
                      </div>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Enter the link you want to check for phishing attempts.
                  </p>
                </div>
                
                <div className="flex justify-center">
                  {/* Only the styled Submit button */}
                  <HoverBorderGradient
                    onClick={handleButtonClick}
                    className="text-base font-medium py-2 px-8 text-gray-900 dark:text-white cursor-pointer"
                    containerClassName="rounded-full"
                    duration={1}
                    as="button"
                    disabled={isLoading}
                    type="button"
                  >
                    {isLoading ? "Processing..." : "Submit"}
                  </HoverBorderGradient>
                </div>
                
                {/* Custom styles for HoverBorderGradient */}
                <style jsx global>{`
                  /* Light theme adjustments for HoverBorderGradient */
                  .bg-black/20 {
                    background-color: rgba(255, 255, 255, 0.2) !important; /* white with opacity */
                  }
                  .dark .bg-white/20 {
                    background-color: rgba(255, 255, 255, 0.2) !important;
                  }
                  
                  /* Button background */
                  .bg-black {
                    background-color: #ffffff !important; /* pure white */
                    border: 1px solid #e2e8f0 !important; /* light border for definition */
                  }
                  .dark .bg-black {
                    background-color: #000 !important; /* pure black */
                  }
                  
                  /* Fix animation visibility */
                  .flex-none {
                    opacity: 1 !important;
                    filter: blur(1px) !important;
                  }
                  
                  /* Ensure rounded corners */
                  .rounded-\\[100px\\] {
                    border-radius: 9999px !important;
                  }
                  
                  /* Enhance hover effect */
                  .hover\\:bg-black\\/10:hover {
                    background-color: rgba(255, 255, 255, 0.9) !important; /* slightly more opaque white */
                  }
                  .dark .hover\\:bg-black\\/10:hover {
                    background-color: rgba(0, 0, 0, 0.1) !important;
                  }
                  
                  /* Override text color */
                  button .text-white {
                    color: #111827 !important; /* gray-900 for light theme */
                  }
                  .dark button .text-white {
                    color: white !important; /* white for dark theme */
                  }
                  
                  /* Fix animation for light traveling across borders */
                  @keyframes gradientMove {
                    0% { background-position: 0% 0; }
                    100% { background-position: 200% 0; }
                  }
                  
                  /* Make sure the animation is visible and running */
                  [class*="HoverBorderGradient"] .flex-none {
                    animation: gradientMove 3s linear infinite !important;
                    background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.8), transparent) !important;
                    background-size: 200% 100% !important;
                    opacity: 0.8 !important;
                  }
                  
                  /* Enhance hover animation */
                  [class*="HoverBorderGradient"]:hover .flex-none {
                    animation: gradientMove 1.5s linear infinite !important;
                    background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 1), transparent) !important;
                    background-size: 200% 100% !important;
                    opacity: 1 !important;
                  }

                  /* MultiStepLoader theme adjustments */
                  .dark .text-black {
                    color: white !important;
                  }
                  .dark .text-lime-500 {
                    color: #84cc16 !important; /* lime-500 */
                  }
                  .text-lime-500 {
                    color: #65a30d !important; /* lime-600 for better contrast in light mode */
                  }
                `}</style>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Loading animation - Moved outside the card for full-screen effect */}
      <MultiStepLoader 
        loadingStates={loadingStates} 
        loading={isLoading}
        duration={2000}
        loop={false}
      />
      
      {/* Results section - Separate from the form for better visibility */}
      {showResults && (
        <motion.div 
          className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-24"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-center text-gray-900 dark:text-white mb-12 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
            {displayText}
          </h2>
          
          {/* Sample result card */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 max-w-2xl mx-auto border border-gray-200 dark:border-gray-700">
            <div className="flex items-center mb-6">
              <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center mr-5">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h4 className="text-2xl font-bold text-gray-800 dark:text-white">High Risk Detected</h4>
                <p className="text-base text-gray-500 dark:text-gray-300">This link shows multiple phishing indicators</p>
              </div>
            </div>
            
            <div className="space-y-4 mt-8">
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-gray-700 dark:text-gray-200 font-medium">Domain Age:</span>
                <span className="font-semibold text-red-500 dark:text-red-400">2 days old</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-gray-700 dark:text-gray-200 font-medium">SSL Certificate:</span>
                <span className="font-semibold text-red-500 dark:text-red-400">Invalid</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-gray-700 dark:text-gray-200 font-medium">Suspicious URL:</span>
                <span className="font-semibold text-red-500 dark:text-red-400">Yes</span>
              </div>
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-gray-700 dark:text-gray-200 font-medium">Blacklist Status:</span>
                <span className="font-semibold text-red-500 dark:text-red-400">Blacklisted</span>
              </div>
            </div>
            
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-600">
              <p className="text-base text-gray-600 dark:text-gray-300 font-medium">
                We recommend not visiting this website as it appears to be a phishing attempt.
              </p>
            </div>
          </div>
        </motion.div>
      )}
    </>
  );
} 