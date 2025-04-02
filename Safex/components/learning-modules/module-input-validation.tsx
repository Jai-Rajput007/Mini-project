"use client";
import Image from "next/image";
import React, { useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOutsideClick } from "@/hooks/use-outside-click";

export default function InputValidationModule() {
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

// Cards for Input Validation module
const cards = [
  {
    description: "Core principles of input validation",
    title: "Validation Basics",
    src: "https://images.unsplash.com/photo-1580894732444-8ecded7900cd?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            Input validation is the process of verifying that user input meets an application's expectations before processing it. Proper validation is a key defense against many security vulnerabilities.
          </p>
          <h4 className="font-bold mt-4 mb-2">Why Input Validation Matters:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Prevents malicious data from causing security vulnerabilities</li>
            <li>Improves data quality and integrity</li>
            <li>Reduces errors and unexpected behaviors</li>
            <li>Defends against common attacks like XSS and injection</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Validation Approaches:</h4>
          <ol className="list-decimal pl-5 space-y-1 mt-2">
            <li><strong>Allowlist (Whitelist) Validation:</strong> Only allow known good input patterns</li>
            <li><strong>Denylist (Blacklist) Validation:</strong> Block known bad patterns (less effective)</li>
            <li><strong>Syntactic Validation:</strong> Verify data follows the correct format (e.g., email, date)</li>
            <li><strong>Semantic Validation:</strong> Verify data makes logical sense (e.g., birth date is in the past)</li>
          </ol>
          <p className="mt-4">
            Input validation should be implemented on both client and server side, with server-side validation being essential as client-side validation can be bypassed.
          </p>
        </div>
      );
    },
  },
  {
    description: "Securing your application form inputs",
    title: "Form Data Validation",
    src: "https://images.unsplash.com/photo-1568952433726-3896e3881c65?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-project-proactive-controls/v3/en/c5-validate-inputs",
    content: () => {
      return (
        <div>
          <p>
            Form data validation is critical for web applications that accept user input. Properly validating form inputs helps prevent common attacks and ensures data quality.
          </p>
          <h4 className="font-bold mt-4 mb-2">Key Form Fields to Validate:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Email addresses:</strong> Use proper format validation with regex</li>
            <li><strong>Names and text fields:</strong> Check for prohibited characters and length limits</li>
            <li><strong>Numbers:</strong> Verify type, range, and format</li>
            <li><strong>Dates:</strong> Ensure logical formats and reasonable ranges</li>
            <li><strong>Passwords:</strong> Enforce complexity requirements</li>
            <li><strong>File uploads:</strong> Verify file types, sizes, and content</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Validation Implementation:</h4>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// Example email validation in JavaScript
function validateEmail(email) {
  const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$/;
  return regex.test(email);
}

// Example server-side validation (pseudo-code)
if (!validateEmail(userInput.email)) {
  return respondWithError("Invalid email format");
}`}
          </pre>
          <p className="mt-4">
            Always implement both client-side validation (for user experience) and server-side validation (for security), as client-side validation can be bypassed by malicious actors.
          </p>
        </div>
      );
    },
  },
  {
    description: "Sanitizing and encoding user inputs",
    title: "Data Sanitization",
    src: "https://images.unsplash.com/photo-1505678261036-a3fcc5e884ee?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html#rule-0-never-insert-untrusted-data-except-in-allowed-locations",
    content: () => {
      return (
        <div>
          <p>
            Data sanitization involves cleaning and transforming input to ensure it's safe for processing. Unlike validation (which rejects invalid input), sanitization modifies input to make it acceptable.
          </p>
          <h4 className="font-bold mt-4 mb-2">Sanitization Techniques:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>HTML Encoding:</strong> Convert special characters to HTML entities</li>
            <li><strong>JavaScript Encoding:</strong> Escape special characters in JavaScript contexts</li>
            <li><strong>URL Encoding:</strong> Convert special characters for safe URL inclusion</li>
            <li><strong>CSS Encoding:</strong> Escape special characters in CSS contexts</li>
            <li><strong>Character Removal:</strong> Remove potentially dangerous characters</li>
            <li><strong>Filtering:</strong> Remove markup or scripting elements</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Context-Specific Sanitization:</h4>
          <p>Sanitization should be context-aware - different encodings are needed depending on where data will be used:</p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// HTML context
const safeHtml = escapeHtml(userInput);
// <div>\${"{safeHtml}"}</div>

// JavaScript context
const safeJs = escapeJs(userInput);
// <script>const userName = "\${"{safeJs}"}";</script>

// URL parameter context
const safeUrl = encodeURIComponent(userInput);
// <a href="https://example.com?q=\${"{safeUrl}"}">Link</a>

// CSS context
const safeCss = escapeCss(userInput);
// <div style="color: \${"{safeCss}"}">Text</div>`}
          </pre>
          <p className="mt-4">
            Always sanitize data both before storing it (if necessary) and before outputting it to users. Use established libraries rather than creating your own sanitization functions.
          </p>
        </div>
      );
    },
  },
  {
    description: "Securely handling file uploads",
    title: "File Upload Validation",
    src: "https://images.unsplash.com/photo-1618044733300-9472054094ee?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2071&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            File upload functionality presents unique security challenges. Without proper validation, attackers can upload malicious files that may lead to server-side code execution or other attacks.
          </p>
          <h4 className="font-bold mt-4 mb-2">File Upload Risks:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Uploading executable server-side code (PHP, ASP, JSP, etc.)</li>
            <li>Uploading malware for distribution</li>
            <li>Uploading extremely large files (Denial of Service)</li>
            <li>Overwriting existing files</li>
            <li>Client-side attacks (XSS via SVG or HTML files)</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">File Upload Validation Strategies:</h4>
          <ol className="list-decimal pl-5 space-y-1 mt-2">
            <li><strong>File Type Validation:</strong>
              <ul className="list-disc pl-5 mt-1">
                <li>Check file extension against an allowlist</li>
                <li>Verify MIME type</li>
                <li>Validate file content (magic bytes/signatures)</li>
              </ul>
            </li>
            <li><strong>File Size Validation:</strong>
              <ul className="list-disc pl-5 mt-1">
                <li>Set maximum file size limits</li>
                <li>Validate before fully uploading the file</li>
              </ul>
            </li>
            <li><strong>File Name Validation:</strong>
              <ul className="list-disc pl-5 mt-1">
                <li>Generate new random filenames</li>
                <li>Remove path information</li>
                <li>Sanitize filenames to remove special characters</li>
              </ul>
            </li>
          </ol>
          <p className="mt-4">
            Store uploaded files outside the web root when possible, and consider using a dedicated storage service like AWS S3 for handling user uploads.
          </p>
        </div>
      );
    },
  },
  {
    description: "Type casting and SQL prevention",
    title: "Advanced Validation Techniques",
    src: "https://images.unsplash.com/photo-1551808525-51a94da548ce?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2233&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            Advanced validation techniques go beyond simple format checking to implement robust security controls for handling complex data inputs and preventing sophisticated attacks.
          </p>
          <h4 className="font-bold mt-4 mb-2">Type Conversion and Casting:</h4>
          <p>
            Force inputs to be of the expected type to prevent type confusion attacks:
          </p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// JavaScript
const id = parseInt(userInput, 10); // Convert to integer
if (isNaN(id) || id <= 0) {
  return respondWithError("Invalid ID");
}

// PHP
$id = (int)$_GET['id']; // Cast to integer

// Python
try:
    user_id = int(request.args.get('id', 0))
except ValueError:
    return error_response("Invalid ID format")`}
          </pre>
          
          <h4 className="font-bold mt-4 mb-2">Parameterized Queries (Prepared Statements):</h4>
          <p>
            Use parameterized queries to safely include user data in database queries:
          </p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// Node.js with MySQL
const query = "SELECT * FROM users WHERE id = ?";
connection.query(query, [userId], function (error, results) {
  // Process results
});

// Python with SQLAlchemy
user = session.query(User).filter(User.id == user_id).first()

// Java with JDBC
PreparedStatement stmt = connection.prepareStatement(
  "SELECT * FROM users WHERE id = ?"
);
stmt.setInt(1, userId);
ResultSet rs = stmt.executeQuery();`}
          </pre>
          
          <h4 className="font-bold mt-4 mb-2">JSON Schema Validation:</h4>
          <p>
            For API endpoints accepting JSON, use JSON Schema to validate structure and types:
          </p>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// JSON Schema example
const userSchema = {
  type: "object",
  required: ["username", "email"],
  properties: {
    username: { type: "string", minLength: 3, maxLength: 50 },
    email: { type: "string", format: "email" },
    age: { type: "integer", minimum: 18 }
  },
  additionalProperties: false
};

// Validate against schema
const validate = ajv.compile(userSchema);
const valid = validate(userData);
if (!valid) {
  return respondWithError(validate.errors);
}`}
          </pre>
          
          <p className="mt-4">
            These advanced techniques should be combined with basic validation practices for comprehensive input security.
          </p>
        </div>
      );
    },
  },
]; 