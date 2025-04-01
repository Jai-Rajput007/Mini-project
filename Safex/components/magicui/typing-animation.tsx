"use client";

import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";

interface TypingAnimationProps {
  children: string;
  className?: string;
  duration?: number;
  delay?: number;
  onTextUpdate?: (text: string) => void;
}

export function TypingAnimation({
  children,
  className,
  duration = 100,
  delay = 0,
  onTextUpdate,
  ...props
}: TypingAnimationProps) {
  // Use regular component for better stability
  const [displayedText, setDisplayedText] = useState<string>("");
  const elementRef = useRef<HTMLDivElement>(null);
  const animationComplete = useRef(false);
  const typingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Simple typing effect
  useEffect(() => {
    // Reset text when component mounts or children change
    setDisplayedText("");
    animationComplete.current = false;
    
    // Clear any existing intervals/timeouts
    if (typingIntervalRef.current) {
      clearInterval(typingIntervalRef.current);
      typingIntervalRef.current = null;
    }
    
    if (startTimeoutRef.current) {
      clearTimeout(startTimeoutRef.current);
      startTimeoutRef.current = null;
    }
    
    // Start typing after specified delay
    startTimeoutRef.current = setTimeout(() => {
      let currentIndex = 0;
      
      // Create typing interval
      typingIntervalRef.current = setInterval(() => {
        if (currentIndex < children.length) {
          const newText = children.substring(0, currentIndex + 1);
          setDisplayedText(newText);
          
          // Call the callback if provided
          if (onTextUpdate) {
            onTextUpdate(newText);
          }
          
          currentIndex++;
        } else {
          // Typing complete
          if (typingIntervalRef.current) {
            clearInterval(typingIntervalRef.current);
            typingIntervalRef.current = null;
          }
          animationComplete.current = true;
        }
      }, duration);
    }, delay);
    
    // Clean up on unmount or when dependencies change
    return () => {
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
        typingIntervalRef.current = null;
      }
      
      if (startTimeoutRef.current) {
        clearTimeout(startTimeoutRef.current);
        startTimeoutRef.current = null;
      }
    };
  }, [children, duration, delay, onTextUpdate]);

  return (
    <div
      ref={elementRef}
      className={cn(
        "text-4xl font-bold leading-[1.2] tracking-[-0.02em]",
        className,
      )}
      {...props}
    >
      {displayedText}
    </div>
  );
}
