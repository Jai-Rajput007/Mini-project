"use client";
import React from "react";
import { motion } from "framer-motion";
import { Shield, Users, Globe } from "lucide-react";

export const MissionSection = ({
  className,
}: {
  className?: string;
}) => {
  const values = [
    {
      icon: Shield,
      title: "Security First",
      description:
        "We prioritize the security of our users above all else, implementing the most advanced protection measures available.",
    },
    {
      icon: Users,
      title: "User Empowerment",
      description:
        "We believe in empowering users with knowledge and tools to protect themselves in an increasingly complex digital landscape.",
    },
    {
      icon: Globe,
      title: "Global Protection",
      description:
        "Our mission extends to protecting users worldwide, regardless of their technical expertise or background.",
    },
  ];

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
            Our Mission
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-lg text-gray-600 dark:text-gray-300"
          >
            At Safex, we're committed to creating a safer digital world by
            providing cutting-edge tools that protect users from phishing and
            other cyber threats. Our mission is to make advanced security
            accessible to everyone.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {values.map((value, index) => (
            <ValueCard key={value.title} value={value} index={index} />
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="mt-16 p-8 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800"
        >
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 text-center">
            Our Vision
          </h3>
          <p className="text-gray-600 dark:text-gray-300 text-center max-w-3xl mx-auto">
            We envision a future where everyone can navigate the digital world
            confidently and securely, free from the fear of phishing attacks and
            other cyber threats. Through innovation, education, and accessible
            tools, we're working to make this vision a reality.
          </p>
        </motion.div>
      </div>
    </section>
  );
};

const ValueCard = ({
  value,
  index,
}: {
  value: {
    icon: React.ElementType;
    title: string;
    description: string;
  };
  index: number;
}) => {
  const Icon = value.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
      className="p-6 bg-white dark:bg-gray-950 rounded-xl shadow-md border border-gray-200 dark:border-gray-800 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 text-primary mb-6 mx-auto">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3 text-center">
        {value.title}
      </h3>
      <p className="text-gray-600 dark:text-gray-300 text-center">
        {value.description}
      </p>
    </motion.div>
  );
}; 