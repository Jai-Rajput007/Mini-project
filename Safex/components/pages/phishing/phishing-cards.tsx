"use client";
import React, { useState } from "react";
import { motion } from "framer-motion";
import Image from "next/image";

interface PhishingCardProps {
  title: string;
  description: string;
  image: string;
  category: string;
  date: string;
}

const PhishingCard: React.FC<PhishingCardProps> = ({
  title,
  description,
  image,
  category,
  date,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      className="group relative h-[400px] md:h-[450px] rounded-xl overflow-hidden bg-white dark:bg-gray-900 shadow-lg border border-gray-200 dark:border-gray-800"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 z-0 overflow-hidden">
        <Image
          src={image}
          alt={title}
          width={600}
          height={400}
          className="w-full h-[200px] object-cover transition-transform duration-500 ease-in-out group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
      </div>

      <div className="absolute top-4 left-4 z-10">
        <span className="inline-block px-3 py-1 text-xs font-medium bg-primary/90 text-white rounded-full">
          {category}
        </span>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-6 z-10">
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-white line-clamp-2">{title}</h3>
          <p className="text-sm text-gray-300 line-clamp-3">{description}</p>
        </div>

        <div className="mt-4 flex justify-between items-center">
          <span className="text-xs text-gray-400">{date}</span>
          <motion.button
            className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Learn More
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

export default function PhishingCards() {
  const phishingAttacks = [
    {
      id: 1,
      title: "The Yahoo Data Breach",
      description:
        "One of the largest data breaches in history, affecting over 3 billion Yahoo accounts. Hackers gained access to names, email addresses, telephone numbers, and hashed passwords.",
      image: "/Attacked.jpg",
      category: "Data Breach",
      date: "2013-2014",
    },
    {
      id: 2,
      title: "The Equifax Hack",
      description:
        "A major cybersecurity incident that exposed sensitive personal information of approximately 147 million people, including Social Security numbers, birth dates, and addresses.",
      image: "/Ransomeware.jpg",
      category: "Data Breach",
      date: "2017",
    },
    {
      id: 3,
      title: "WannaCry Ransomware Attack",
      description:
        "A global ransomware attack that targeted computers running Microsoft Windows by encrypting data and demanding ransom payments in Bitcoin. It affected over 200,000 computers across 150 countries.",
      image: "/Attacked.jpg",
      category: "Ransomware",
      date: "May 2017",
    },
    {
      id: 4,
      title: "The SolarWinds Supply Chain Attack",
      description:
        "A sophisticated supply chain attack where hackers compromised the software development environment of SolarWinds, inserting malicious code into software updates distributed to thousands of organizations.",
      image: "/Ransomeware.jpg",
      category: "Supply Chain Attack",
      date: "2020",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {phishingAttacks.map((attack) => (
        <PhishingCard
          key={attack.id}
          title={attack.title}
          description={attack.description}
          image={attack.image}
          category={attack.category}
          date={attack.date}
        />
      ))}
    </div>
  );
} 