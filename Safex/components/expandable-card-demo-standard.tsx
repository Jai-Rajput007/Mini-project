"use client";
import Image from "next/image";
import React, { useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOutsideClick } from "@/hooks/use-outside-click";

export default function ExpandableCardDemo() {
  const [mounted, setMounted] = useState(false);
  const [active, setActive] = useState<(typeof cards)[number] | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const id = useId();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setActive(null);
      }
    };

    if (active) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    } else {
      document.body.style.overflow = "auto";
    }

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [active]);

  // Don't render anything until mounted
  if (!mounted) return null;

  // Handle closing the expanded card
  const handleClose = () => {
    // Use a quick timeout to ensure smooth transition
    setTimeout(() => {
      setActive(null);
    }, 10);
  };

  return (
    <>
      <AnimatePresence>
        {active && typeof active === "object" && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/20 h-full w-full z-10"
            onClick={handleClose}
          />
        )}
      </AnimatePresence>
      
      <AnimatePresence mode="wait">
        {active && typeof active === "object" ? (
          <motion.div 
            key="expanded-card"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="fixed inset-0 grid place-items-center z-[100]"
          >
            <motion.button
              key={`button-${active.title}-${id}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="flex absolute top-2 right-2 lg:hidden items-center justify-center bg-white rounded-full h-6 w-6"
              onClick={handleClose}
            >
              <CloseIcon />
            </motion.button>
            <div
              ref={ref}
              className="w-full max-w-[500px] h-full md:h-fit md:max-h-[90%] flex flex-col bg-white dark:bg-neutral-900 sm:rounded-3xl overflow-hidden"
            >
              <div>
                <Image
                  priority
                  width={200}
                  height={200}
                  src={active.src}
                  alt={active.title}
                  className="w-full h-80 lg:h-80 sm:rounded-tr-lg sm:rounded-tl-lg object-cover object-top"
                />
              </div>
              <div>
                <div className="flex justify-between items-start p-4">
                  <div>
                    <h3 className="font-bold text-neutral-700 dark:text-neutral-200">
                      {active.title}
                    </h3>
                    <p className="text-neutral-600 dark:text-neutral-400">
                      {active.description}
                    </p>
                  </div>
                  <a
                    href={active.ctaLink}
                    target="_blank"
                    className="px-4 py-3 text-sm rounded-full font-bold bg-green-500 text-white"
                  >
                    {active.ctaText}
                  </a>
                </div>
                <div className="pt-4 relative px-4 max-h-[250px] overflow-y-auto pb-6">
                  <div
                    className="text-neutral-600 text-xs md:text-sm lg:text-base flex flex-col items-start gap-4 dark:text-neutral-400"
                  >
                    {typeof active.content === "function" ? active.content() : active.content}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className="w-full p-6 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800 rounded-xl shadow-lg border border-gray-200 dark:border-neutral-700">
        <ul className="max-w-3xl mx-auto space-y-4">
          {cards.map((card, index) => (
            <motion.div
              key={`card-${card.title}-${index}`}
              onClick={() => !active && setActive(card)}
              className="p-4 flex justify-between items-center bg-white dark:bg-neutral-900 rounded-lg cursor-pointer w-full shadow-md hover:shadow-lg transition-all duration-300 border border-gray-100 dark:border-neutral-800 group"
              whileHover={{ 
                y: -8,
                scale: 1.02,
                transition: { duration: 0.2 }
              }}
            >
              <div className="flex items-center gap-3 w-full">
                <div className="relative">
                  <Image
                    width={100}
                    height={100}
                    src={card.src}
                    alt={card.title}
                    className="h-12 w-12 rounded-lg object-cover object-top transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-neutral-800 dark:text-neutral-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300">
                    {card.title}
                  </h3>
                  <p className="text-neutral-600 dark:text-neutral-400 text-sm">
                    {card.description}
                  </p>
                </div>
              </div>
              <button className="px-4 py-2 text-sm rounded-full font-bold bg-gray-100 dark:bg-neutral-800 text-black dark:text-white hover:bg-green-500 hover:text-white transition-all duration-300 ml-3">
                {card.ctaText}
              </button>
            </motion.div>
          ))}
        </ul>
      </div>
    </>
  );
}

export const CloseIcon = () => {
  return (
    <motion.svg
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.05 } }}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-4 w-4 text-black"
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M18 6l-12 12" />
      <path d="M6 6l12 12" />
    </motion.svg>
  );
};

// Create completely separate card data for each learning module
const cards = [
  {
    description: "Fundamentals of Web Security",
    title: "Web Security Basics",
    src: "https://images.unsplash.com/photo-1563206767-5b18f218e8de?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2069&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-project-top-ten/",
    content: () => {
      return (
        <div>
          <p>
            Web security basics are essential knowledge for anyone working with web applications. This comprehensive module covers the fundamental concepts, common vulnerabilities, and best practices for securing web applications.
          </p>
          <h4 className="font-bold mt-4 mb-2">Key Topics:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>Understanding the HTTP protocol and its security implications</li>
            <li>Common attack vectors (XSS, CSRF, SQL Injection)</li>
            <li>The Same-Origin Policy and CORS</li>
            <li>Authentication and Authorization fundamentals</li>
            <li>Secure communication with HTTPS</li>
            <li>Input validation and sanitization</li>
            <li>Session management and cookies</li>
          </ul>
          <p className="mt-4">
            By the end of this module, you'll have a solid understanding of the core principles that form the foundation of web security, enabling you to identify common vulnerabilities and implement appropriate protections.
          </p>
        </div>
      );
    },
  },
  {
    description: "Identify and prevent common attacks",
    title: "Cross-Site Scripting (XSS) Defense",
    src: "https://images.unsplash.com/photo-1510915228340-29c85a43dcfe?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            Cross-Site Scripting (XSS) remains one of the most prevalent web application security vulnerabilities. This module provides in-depth knowledge on how to identify, prevent, and mitigate XSS attacks.
          </p>
          <h4 className="font-bold mt-4 mb-2">Types of XSS:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Reflected XSS:</strong> Malicious script comes from the current HTTP request</li>
            <li><strong>Stored XSS:</strong> Malicious script is stored on the target server</li>
            <li><strong>DOM-based XSS:</strong> Vulnerability exists in client-side code</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Prevention Techniques:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>Output encoding/escaping for different contexts (HTML, CSS, JavaScript, URLs)</li>
            <li>Content Security Policy (CSP) implementation</li>
            <li>Input validation and sanitization</li>
            <li>HttpOnly and Secure cookie flags</li>
            <li>Modern framework protections</li>
          </ul>
          <p className="mt-4">
            This comprehensive guide will help you understand how attackers exploit XSS vulnerabilities and equip you with the knowledge to build robust defenses against these attacks.
          </p>
        </div>
      );
    },
  },
  {
    description: "Protect your databases from injection attacks",
    title: "SQL Injection Prevention",
    src: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            SQL Injection attacks can lead to unauthorized data access, data theft, and even complete system compromise. This module focuses on understanding and preventing SQL injection vulnerabilities.
          </p>
          <h4 className="font-bold mt-4 mb-2">Key Concepts:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>How SQL injection attacks work</li>
            <li>Different types of SQL injection (Error-based, Union-based, Blind, etc.)</li>
            <li>Common injection points in web applications</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Prevention Strategies:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Parameterized Queries:</strong> Using prepared statements with parameterized queries</li>
            <li><strong>ORM Frameworks:</strong> Leveraging ORM frameworks that handle SQL safely</li>
            <li><strong>Input Validation:</strong> Implementing strict input validation</li>
            <li><strong>Stored Procedures:</strong> Using stored procedures with parameterized inputs</li>
            <li><strong>Least Privilege:</strong> Applying principle of least privilege to database accounts</li>
            <li><strong>WAF Protection:</strong> Implementing Web Application Firewall rules</li>
          </ul>
          <p className="mt-4">
            By the end of this module, you'll understand how to identify SQL injection vulnerabilities in your code and implement proper defenses to protect your application's data.
          </p>
        </div>
      );
    },
  },
  {
    description: "Advanced security concepts and defensive programming",
    title: "Secure Coding Practices",
    src: "https://images.unsplash.com/photo-1555066931-4365d14bab8c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/",
    content: () => {
      return (
        <div>
          <p>
            Secure coding practices are essential for building robust and secure applications. This module covers advanced techniques and best practices that go beyond basic security knowledge.
          </p>
          <h4 className="font-bold mt-4 mb-2">Secure Coding Principles:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Defense in Depth:</strong> Implementing multiple layers of security controls</li>
            <li><strong>Fail Secure:</strong> Ensuring systems fail in a secure state</li>
            <li><strong>Least Privilege:</strong> Providing only the minimum necessary access</li>
            <li><strong>Separation of Duties:</strong> Dividing critical functions among different entities</li>
            <li><strong>Economy of Mechanism:</strong> Keeping security implementations simple</li>
            <li><strong>Complete Mediation:</strong> Checking every access to resources</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Advanced Topics:</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>Secure API design patterns</li>
            <li>Memory safety and buffer overflow prevention</li>
            <li>Race condition identification and prevention</li>
            <li>Cryptography best practices</li>
            <li>Secure session management</li>
            <li>Error handling and information leakage prevention</li>
            <li>Secure configuration management</li>
          </ul>
          <p className="mt-4">
            This module provides actionable guidelines for implementing security throughout the software development lifecycle, from requirements gathering to deployment and maintenance.
          </p>
        </div>
      );
    },
  },
];

