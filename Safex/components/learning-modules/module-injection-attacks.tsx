"use client";
import Image from "next/image";
import React, { useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOutsideClick } from "@/hooks/use-outside-click";

export default function InjectionAttacksModule() {
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

// Cards for Injection Attacks module
const cards = [
  {
    description: "Understanding the basics",
    title: "SQL Injection Fundamentals",
    src: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            SQL Injection is one of the most common and dangerous web application security vulnerabilities. It occurs when untrusted data is sent to an interpreter as part of a command or query.
          </p>
          <h4 className="font-bold mt-4 mb-2">How SQL Injection Works:</h4>
          <p>
            In SQL injection attacks, malicious SQL statements are inserted into entry fields for execution by the backend database. When successful, attackers can:
          </p>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Read sensitive data from the database</li>
            <li>Modify database data (insert/update/delete)</li>
            <li>Execute administration operations on the database</li>
            <li>Recover the content of a given file</li>
            <li>In some cases, issue commands to the operating system</li>
          </ul>
          <p className="mt-4">
            A common example is manipulating a login form by entering <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">username' OR '1'='1</code> in the username field, which might trick the system into authenticating without a valid password.
          </p>
        </div>
      );
    },
  },
  {
    description: "Server-side execution vulnerabilities",
    title: "Command Injection",
    src: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2068&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-community/attacks/Command_Injection",
    content: () => {
      return (
        <div>
          <p>
            Command Injection is an attack where an attacker attempts to execute arbitrary commands on the host operating system via a vulnerable web application.
          </p>
          <h4 className="font-bold mt-4 mb-2">How It Works:</h4>
          <p>
            This vulnerability occurs when an application passes unsafe user-supplied data to a system shell. If the application doesn't properly sanitize the data, an attacker can inject commands that will execute on the operating system.
          </p>
          <h4 className="font-bold mt-4 mb-2">Examples:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Adding a semicolon followed by another command: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">ping example.com; ls -la</code></li>
            <li>Using command separators like <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">&&</code> or <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">||</code></li>
            <li>Using backticks or $(command) to execute nested commands</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Prevention:</h4>
          <p>
            Avoid using system commands when possible. If necessary, use parameterized APIs, validate input tightly, and run with minimal privileges.
          </p>
        </div>
      );
    },
  },
  {
    description: "Server-side code execution",
    title: "Code Injection",
    src: "https://images.unsplash.com/photo-1542903660-eedba2cda473?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-community/attacks/Code_Injection",
    content: () => {
      return (
        <div>
          <p>
            Code Injection is a security vulnerability that allows an attacker to inject and then execute arbitrary code in the context of the application. This is different from command injection as it involves the execution of programming code rather than system commands.
          </p>
          <h4 className="font-bold mt-4 mb-2">Vulnerable Functions:</h4>
          <p>
            Many languages have functions that can execute code dynamically:
          </p>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>PHP: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">eval()</code>, <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">assert()</code>, <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">system()</code></li>
            <li>JavaScript: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">eval()</code>, <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">setTimeout()</code> with string argument</li>
            <li>Python: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">eval()</code>, <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">exec()</code></li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Example:</h4>
          <p>
            If a PHP application uses code like <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">eval('$result = ' . $_GET['formula']);</code> to evaluate a mathematical formula from user input, an attacker could send <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">formula=1; system('ls -la')</code> to execute arbitrary commands.
          </p>
          <h4 className="font-bold mt-4 mb-2">Prevention:</h4>
          <p>
            Avoid using dynamic code execution functions. Use safer alternatives like mathematical libraries for calculations or template engines for rendering content.
          </p>
        </div>
      );
    },
  },
  {
    description: "Database access risks",
    title: "NoSQL Injection",
    src: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05.6-Testing_for_NoSQL_Injection",
    content: () => {
      return (
        <div>
          <p>
            NoSQL Injection is similar to SQL injection but targets non-relational (NoSQL) databases like MongoDB, Cassandra, or CouchDB. Instead of SQL syntax, attackers manipulate query operators specific to the NoSQL database.
          </p>
          <h4 className="font-bold mt-4 mb-2">How NoSQL Injection Works:</h4>
          <p>
            NoSQL databases often use JSON or similar formats for queries. Attackers can inject query operators to change the logic of the intended query.
          </p>
          <h4 className="font-bold mt-4 mb-2">MongoDB Example:</h4>
          <p>
            For a login query like: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">db.users.find(&#123;username: "user", password: "pass"&#125;)</code>
          </p>
          <p className="mt-2">
            An attacker might send:
          </p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2">
{`{
  "username": {"$ne": null},
  "password": {"$ne": null}
}`}
          </pre>
          <p className="mt-2">
            The <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">$ne</code> operator means "not equal," causing the query to return users where username and password are not null (potentially all users).
          </p>
          <h4 className="font-bold mt-4 mb-2">Prevention:</h4>
          <p>
            Use parameterized queries, validate input type and structure, and implement appropriate access controls.
          </p>
        </div>
      );
    },
  },
  {
    description: "JavaScript template risks",
    title: "Template Injection",
    src: "https://images.unsplash.com/photo-1516259762381-22954d7d3ad2?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2089&q=80",
    ctaText: "Learn",
    ctaLink: "https://portswigger.net/web-security/server-side-template-injection",
    content: () => {
      return (
        <div>
          <p>
            Server-Side Template Injection (SSTI) is a vulnerability that occurs when user input is embedded directly into a template engine. This can lead to remote code execution on the server.
          </p>
          <h4 className="font-bold mt-4 mb-2">Vulnerable Template Engines:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Jinja2/Twig (Python/PHP)</li>
            <li>Handlebars (JavaScript)</li>
            <li>EJS (JavaScript)</li>
            <li>FreeMarker (Java)</li>
            <li>Velocity (Java)</li>
            <li>ERB (Ruby)</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Example Attack:</h4>
          <p>
            If a Jinja2 template uses: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">render_template_string("Hello " + username)</code>
          </p>
          <p className="mt-2">
            An attacker might input: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded-sm">&#123;&#123;7*7&#125;&#125;</code>
          </p>
          <p className="mt-2">
            If the output shows "Hello 49", the application is vulnerable to SSTI.
          </p>
          <p className="mt-2">
            More dangerous payloads could execute arbitrary code:
          </p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2">
{`{{ config.__class__.__init__.__globals__['os'].popen('ls').read() }}`}
          </pre>
          <h4 className="font-bold mt-4 mb-2">Prevention:</h4>
          <p>
            Never use user input directly in template syntax. Sanitize and validate all inputs, use a sandboxed template environment, and consider template logic on the client side instead.
          </p>
        </div>
      );
    },
  },
]; 