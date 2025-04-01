"use client";
import React, { useRef } from "react";
import { motion, useInView } from "framer-motion";

interface TimelineEvent {
  year: string;
  title: string;
  description: string;
}

export const HistoryTimeline = ({
  events,
  className,
}: {
  events: TimelineEvent[];
  className?: string;
}) => {
  return (
    <section className={`py-16 ${className || ""}`}>
      <div className="container mx-auto px-4">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4"
          >
            Our Journey
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-lg text-gray-600 dark:text-gray-300"
          >
            From our humble beginnings to where we are today, this timeline
            highlights the key milestones in our mission to create a safer
            digital world.
          </motion.p>
        </div>

        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-1/2 transform -translate-x-1/2 h-full w-1 bg-gray-200 dark:bg-gray-800"></div>

          {events.map((event, index) => (
            <TimelineItem
              key={index}
              event={event}
              index={index}
              isLeft={index % 2 === 0}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

const TimelineItem = ({
  event,
  index,
  isLeft,
}: {
  event: TimelineEvent;
  index: number;
  isLeft: boolean;
}) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });

  return (
    <div className="relative mb-16 last:mb-0">
      <div
        ref={ref}
        className={`flex items-center justify-center ${
          isLeft ? "md:justify-end" : "md:justify-start"
        } relative z-10`}
      >
        <motion.div
          initial={{ opacity: 0, x: isLeft ? 50 : -50 }}
          animate={isInView ? { opacity: 1, x: 0 } : {}}
          transition={{ duration: 0.5, delay: 0.2 }}
          className={`w-full md:w-5/12 ${isLeft ? "md:mr-8" : "md:ml-8"}`}
        >
          <div className="p-6 bg-white dark:bg-gray-950 rounded-xl shadow-md border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                {event.year}
              </div>
              <h3 className="ml-4 text-xl font-semibold text-gray-900 dark:text-white">
                {event.title}
              </h3>
            </div>
            <p className="text-gray-600 dark:text-gray-300">
              {event.description}
            </p>
          </div>
        </motion.div>
      </div>

      {/* Circle marker on the timeline */}
      <div className="absolute left-1/2 transform -translate-x-1/2 w-6 h-6 rounded-full bg-primary border-4 border-white dark:border-gray-950 z-10"></div>
    </div>
  );
}; 