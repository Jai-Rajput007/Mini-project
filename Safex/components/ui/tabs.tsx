"use client";

import * as React from 'react';
import * as TabsPrimitive from '@radix-ui/react-tabs';
import { useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

type Tab = {
  title: string;
  value: string;
  content?: string | React.ReactNode | any;
};

const Tabs = TabsPrimitive.Root;

const TabsList = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={`inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500 dark:bg-gray-800 dark:text-gray-400 ${className}`}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-white data-[state=active]:text-gray-950 data-[state=active]:shadow-sm dark:ring-offset-gray-950 dark:focus-visible:ring-gray-800 dark:data-[state=active]:bg-gray-950 dark:data-[state=active]:text-gray-50 ${className}`}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = React.forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={`mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2 dark:ring-offset-gray-950 dark:focus-visible:ring-gray-800 ${className}`}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };

// Custom TabContainer component to handle containerClassName prop
const TabContainer = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { containerClassName?: string }
>(({ containerClassName, className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "flex flex-row items-center justify-start [perspective:1000px] relative overflow-auto sm:overflow-visible no-visible-scrollbar max-w-full w-full",
      containerClassName || className
    )}
    {...props}
  />
));
TabContainer.displayName = "TabContainer";

// Custom TabButton component to handle tabClassName prop
const TabButton = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & { 
    tabClassName?: string;
    isHighlighted?: boolean;
    activeTabClassName?: string;
  }
>(({ tabClassName, isHighlighted, activeTabClassName, className, children, ...props }, ref) => (
  <button
    ref={ref}
    className={cn("relative px-4 py-2 rounded-full flex items-center justify-center", tabClassName || className)}
    style={{
      transformStyle: "preserve-3d",
    }}
    {...props}
  >
    {isHighlighted && (
      <motion.div
        layoutId="tab-highlight"
        transition={{
          type: "spring",
          stiffness: 400,
          damping: 40,
          mass: 0.5,
        }}
        className={cn(
          "absolute inset-0 bg-gray-200 dark:bg-zinc-800 rounded-full",
          activeTabClassName
        )}
        style={{
          width: "100%",
          height: "100%"
        }}
      />
    )}
    {children}
  </button>
));
TabButton.displayName = "TabButton";

export const AnimatedTabs = ({
  tabs: propTabs,
  containerClassName,
  activeTabClassName,
  tabClassName,
  contentClassName,
  onValueChange,
  currentRoute, // New prop to sync with current page
}: {
  tabs: Tab[];
  containerClassName?: string;
  activeTabClassName?: string;
  tabClassName?: string;
  contentClassName?: string;
  onValueChange?: (value: string) => void;
  currentRoute?: string;
}) => {
  // Find the tab that matches the current route
  const findActiveTab = () => {
    if (!currentRoute) return propTabs[0];
    const matchingTab = propTabs.find((tab) => tab.value === currentRoute);
    return matchingTab || propTabs[0];
  };

  const [active, setActive] = useState<Tab>(findActiveTab());
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);
  const [tabs, setTabs] = useState<Tab[]>(propTabs);
  const [hovering, setHovering] = useState(false);

  // Update active tab when currentRoute changes
  useEffect(() => {
    const newActiveTab = findActiveTab();
    setActive(newActiveTab);
    
    // Reorder tabs to put active tab first
    const newTabs = [...propTabs];
    const activeIndex = newTabs.findIndex(tab => tab.value === newActiveTab.value);
    if (activeIndex > 0) {
      const [activeTab] = newTabs.splice(activeIndex, 1);
      newTabs.unshift(activeTab);
      setTabs(newTabs);
    }
  }, [currentRoute, propTabs]);

  // Debounce hover updates
  const debounce = (func: (...args: any[]) => void, wait: number) => {
    let timeout: NodeJS.Timeout;
    return (...args: any[]) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  };

  const debouncedSetHoveredTab = useCallback(
    debounce((value: string | null) => {
      setHoveredTab(value);
    }, 50),
    []
  );

  const moveSelectedTabToTop = (idx: number) => {
    const newTabs = [...propTabs];
    const selectedTab = newTabs.splice(idx, 1);
    newTabs.unshift(selectedTab[0]);
    setTabs(newTabs);
    setActive(newTabs[0]);
    setHoveredTab(null); // Clear hover on click
    onValueChange?.(newTabs[0].value);
  };

  // Highlight follows hover, falls back to active (current page)
  const highlightedTab = hoveredTab || active.value;

  return (
    <div
      className={cn(
        "flex flex-row items-center justify-start [perspective:1000px] relative overflow-auto sm:overflow-visible no-visible-scrollbar max-w-full w-full",
        containerClassName
      )}
      onMouseLeave={() => {
        debouncedSetHoveredTab(null); // Reset hover when leaving the container
        setHovering(false);
      }}
    >
      {propTabs.map((tab, idx) => (
        <button
          key={tab.title}
          onClick={() => moveSelectedTabToTop(idx)}
          onMouseEnter={() => {
            debouncedSetHoveredTab(tab.value);
            setHovering(true);
          }}
          className={cn("relative px-4 py-2 rounded-full flex items-center justify-center", tabClassName)}
          style={{
            transformStyle: "preserve-3d",
          }}
        >
          {highlightedTab === tab.value && (
            <motion.div
              layoutId="tab-highlight"
              transition={{
                type: "spring",
                stiffness: 400,
                damping: 40,
                mass: 0.5,
              }}
              className={cn(
                "absolute inset-0 bg-gray-200 dark:bg-zinc-800 rounded-full",
                activeTabClassName
              )}
              style={{
                width: "100%",
                height: "100%"
              }}
            />
          )}
          <span className="relative block text-black dark:text-white whitespace-nowrap">
            {tab.title}
          </span>
        </button>
      ))}
      <div 
        className={cn("relative w-full h-full mt-32", contentClassName)}
      >
        {tabs.map((tab, idx) => (
          <motion.div
            key={tab.value}
            layoutId={tab.value}
            style={{
              scale: 1 - idx * 0.1,
              top: hovering ? idx * -50 : 0,
              zIndex: -idx,
              opacity: idx < 3 ? 1 - idx * 0.1 : 0,
            }}
            animate={{
              y: tab.value === active.value ? [0, 40, 0] : 0,
            }}
            className={cn("w-full h-full absolute top-0 left-0")}
          >
            {tab.content}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export const FadeInDiv = ({
  className,
  tabs,
  active,
  hovering,
}: {
  className?: string;
  key?: string;
  tabs: Tab[];
  active: Tab;
  hovering?: boolean;
}) => {
  const isActive = (tab: Tab) => {
    return tab.value === active.value;
  };
  return (
    <div className="relative w-full h-full">
      {tabs.map((tab, idx) => (
        <motion.div
          key={tab.value}
          layoutId={tab.value}
          style={{
            scale: 1 - idx * 0.1,
            top: hovering ? idx * -50 : 0,
            zIndex: -idx,
            opacity: idx < 3 ? 1 - idx * 0.1 : 0,
          }}
          animate={{
            y: isActive(tab) ? [0, 40, 0] : 0,
          }}
          className={cn("w-full h-full absolute top-0 left-0", className)}
        >
          {tab.content}
        </motion.div>
      ))}
    </div>
  );
};