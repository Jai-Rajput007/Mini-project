"use client";
import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Quote } from "lucide-react";
import Image from "next/image";

interface Testimonial {
  id: number;
  name: string;
  role: string;
  company: string;
  content: string;
  avatar: string;
}

export const TestimonialCarousel = ({
  testimonials,
  autoplayInterval = 5000,
  className,
}: {
  testimonials: Testimonial[];
  autoplayInterval?: number;
  className?: string;
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoplay, setIsAutoplay] = useState(true);

  const nextTestimonial = useCallback(() => {
    setCurrentIndex((prevIndex) =>
      prevIndex === testimonials.length - 1 ? 0 : prevIndex + 1
    );
  }, [testimonials.length]);

  const prevTestimonial = useCallback(() => {
    setCurrentIndex((prevIndex) =>
      prevIndex === 0 ? testimonials.length - 1 : prevIndex - 1
    );
  }, [testimonials.length]);

  useEffect(() => {
    if (!isAutoplay) return;

    const interval = setInterval(() => {
      nextTestimonial();
    }, autoplayInterval);

    return () => clearInterval(interval);
  }, [isAutoplay, nextTestimonial, autoplayInterval]);

  const handleMouseEnter = () => setIsAutoplay(false);
  const handleMouseLeave = () => setIsAutoplay(true);

  return (
    <div
      className={`relative overflow-hidden ${className || ""}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="absolute top-1/2 left-4 z-10 -translate-y-1/2">
        <button
          onClick={prevTestimonial}
          className="p-2 rounded-full bg-white/10 backdrop-blur-sm text-gray-800 dark:text-white hover:bg-white/20 transition-colors"
          aria-label="Previous testimonial"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
      </div>

      <div className="absolute top-1/2 right-4 z-10 -translate-y-1/2">
        <button
          onClick={nextTestimonial}
          className="p-2 rounded-full bg-white/10 backdrop-blur-sm text-gray-800 dark:text-white hover:bg-white/20 transition-colors"
          aria-label="Next testimonial"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      <div className="relative h-[400px] md:h-[300px] w-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 flex flex-col md:flex-row items-center p-6 md:p-10 bg-white dark:bg-gray-950 rounded-xl shadow-md"
          >
            <div className="mb-6 md:mb-0 md:mr-10 flex-shrink-0">
              <div className="relative w-20 h-20 md:w-24 md:h-24 rounded-full overflow-hidden border-4 border-primary/20">
                <Image
                  src={testimonials[currentIndex].avatar}
                  alt={testimonials[currentIndex].name}
                  fill
                  className="object-cover"
                />
              </div>
            </div>

            <div className="flex-1">
              <Quote className="w-10 h-10 text-primary/20 mb-4" />
              <p className="text-gray-700 dark:text-gray-300 mb-6 italic">
                "{testimonials[currentIndex].content}"
              </p>
              <div>
                <h4 className="font-medium text-gray-900 dark:text-white">
                  {testimonials[currentIndex].name}
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {testimonials[currentIndex].role},{" "}
                  {testimonials[currentIndex].company}
                </p>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="flex justify-center mt-6 space-x-2">
        {testimonials.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              index === currentIndex
                ? "bg-primary w-6"
                : "bg-gray-300 dark:bg-gray-700"
            }`}
            aria-label={`Go to testimonial ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
}; 