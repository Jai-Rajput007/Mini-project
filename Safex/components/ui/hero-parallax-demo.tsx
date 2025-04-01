"use client";
import React from "react";
import { HeroParallax } from "@/components/ui/hero-parallax";

export default function HeroParallaxDemo() {
  return <HeroParallax products={products} />;
}

export const products = [
  {
    title: "Data Breaches",
    link: "https://www.ftc.gov/business-guidance/resources/data-breach-response-guide-business",
    thumbnail:
      "/7.jpg",
  },
  {
    title: "Cybersecurity Attacks",
    link: "https://thehackernews.com/",
    thumbnail:
      "/2.png",
  },
  {
    title: "Ransomeware Attacks",
    link: "https://cybersecurityventures.com/ransomware-report/",
    thumbnail:
      "/Ransomeware.jpg",
  },
  {
    title: "Statistics",
    link: "https://www.embroker.com/blog/cyber-attack-statistics/",
    thumbnail:
      "/3.jpg",
  },
  {
    title: "Cyber Incidents",
    link: "https://blog.checkpoint.com/research/a-closer-look-at-q3-2024-75-surge-in-cyber-attacks-worldwide/",
    thumbnail:
      "/4.png",
  },
  {
    title: "Employement",
    link: "https://www.techtarget.com/whatis/feature/5-top-cybersecurity-careers",
    thumbnail:
      "/5.jpg",
  },
  {
    title: "Medusa",
    link: "https://www.tripwire.com/state-of-security/medusa-ransomware-what-you-need-know",
    thumbnail:
      "/6.png",
  },
  {
    title: "Recent Attacks",
    link: "https://www.csis.org/programs/strategic-technologies-program/significant-cyber-incidents",
    thumbnail:
      "/1.png",
  },
  {
    title: "Threats",
    link: "https://nordlayer.com/blog/futurespective-2033-cyberthreats/",
    thumbnail:
      "/8.jpg",
  },
  {
    title: "Common Cyber Attacks",
    link: "https://www.simplilearn.com/tutorials/cyber-security-tutorial/types-of-cyber-attacks",
    thumbnail:
      "/9.png",
  },
  {
    title: "Sectors Affected",
    link: "https://www.eccu.edu/blog/cybersecurity/top-industries-most-vulnerable-to-cyber-attacks/",
    thumbnail:
      "/10.jpg",
  },
  {
    title: "Countries",
    link: "https://mixmode.ai/blog/global-cybercrime-report-2024-which-countries-face-the-highest-risk/",
    thumbnail:
      "/11.png",
  },
  {
    title: "Types of cyber attacks",
    link: "https://www.fortinet.com/resources/cyberglossary/types-of-cyber-attacks",
    thumbnail:
      "/12.png",
  },
  {
    title: "Protection against Ransomware",
    link: "https://www.cisa.gov/stopransomware/how-can-i-protect-against-ransomware",
    thumbnail:
      "/15.jpg",
  },
  {
    title: "Phishing",
    link: "https://www.ncsc.gov.uk/guidance/phishing",
    thumbnail:
      "/14.jpg",
  },
];