"use client";
import React, { useEffect, useRef, useState } from "react";
import { motion, useInView, useMotionValue, useSpring } from "framer-motion";

export const AnimatedCounter = ({
  value,
  direction = "up",
  formatValue = (value: number) => `${value.toLocaleString()}`,
  className,
}: {
  value: number;
  direction?: "up" | "down";
  formatValue?: (value: number) => string;
  className?: string;
}) => {
  const ref = useRef<HTMLSpanElement>(null);
  const motionValue = useMotionValue(direction === "down" ? value : 0);
  const springValue = useSpring(motionValue, {
    damping: 50,
    stiffness: 100,
  });
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const [counter, setCounter] = useState(direction === "down" ? value : 0);

  useEffect(() => {
    if (isInView) {
      motionValue.set(direction === "down" ? 0 : value);
    }
  }, [motionValue, isInView, value, direction]);

  useEffect(() => {
    const unsubscribe = springValue.on("change", (latest) => {
      if (direction === "down") {
        setCounter(value - latest);
      } else {
        setCounter(latest);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [springValue, value, direction]);

  return (
    <span ref={ref} className={className}>
      {formatValue(Math.floor(counter))}
    </span>
  );
};

export const StatsGrid = ({
  stats,
  className,
}: {
  stats: {
    title: string;
    value: number;
    suffix?: string;
    prefix?: string;
  }[];
  className?: string;
}) => {
  return (
    <div
      className={`grid grid-cols-2 md:grid-cols-4 gap-6 ${className || ""}`}
    >
      {stats.map((stat, index) => (
        <div
          key={stat.title}
          className="p-6 bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm"
        >
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            {stat.title}
          </p>
          <div className="flex items-baseline">
            {stat.prefix && (
              <span className="text-gray-700 dark:text-gray-300 mr-1">
                {stat.prefix}
              </span>
            )}
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="text-3xl font-bold text-gray-900 dark:text-white"
            >
              <AnimatedCounter value={stat.value} />
            </motion.span>
            {stat.suffix && (
              <span className="text-gray-700 dark:text-gray-300 ml-1">
                {stat.suffix}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}; 