"use client";
import Image from "next/image";
import React, { useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOutsideClick } from "@/hooks/use-outside-click";

export default function AuthenticationSecurityModule() {
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

  if (!mounted) return null;

  const handleClose = () => {
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

const cards = [
  {
    description: "Securing user credentials",
    title: "Password Security",
    src: "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            Password security is the foundation of authentication systems. Implementing proper password policies and storage practices is essential for protecting user accounts.
          </p>
          <h4 className="font-bold mt-4 mb-2">Password Policies:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Enforce minimum length (at least 12 characters recommended)</li>
            <li>Require complexity (combination of uppercase, lowercase, numbers, special characters)</li>
            <li>Check against common password lists</li>
            <li>Prevent password reuse</li>
            <li>Implement account lockout after failed attempts</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Secure Storage:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Never store passwords in plaintext</li>
            <li>Use strong, slow hashing algorithms (bcrypt, Argon2, PBKDF2)</li>
            <li>Add unique salt for each password</li>
            <li>Implement pepper (server-side secret) for additional security</li>
          </ul>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// Example using bcrypt (Node.js)
const bcrypt = require('bcrypt');
const saltRounds = 12;

// Hashing a password
const hashedPassword = await bcrypt.hash(plainTextPassword, saltRounds);

// Verifying a password
const isMatch = await bcrypt.compare(attemptedPassword, hashedPassword);`}
          </pre>
          <h4 className="font-bold mt-4 mb-2">Additional Considerations:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Enable secure password reset mechanisms</li>
            <li>Implement breached password detection</li>
            <li>Educate users on creating strong passwords</li>
            <li>Consider offering password managers</li>
          </ul>
        </div>
      );
    },
  },
  {
    description: "Beyond passwords for security",
    title: "Multi-Factor Authentication",
    src: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://www.nist.gov/itl/applied-cybersecurity/tig/back-basics-multi-factor-authentication",
    content: () => {
      return (
        <div>
          <p>
            Multi-Factor Authentication (MFA) adds additional layers of security by requiring users to provide multiple forms of verification before gaining access to a system or application.
          </p>
          <h4 className="font-bold mt-4 mb-2">Authentication Factors:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Something you know:</strong> Passwords, PINs, security questions</li>
            <li><strong>Something you have:</strong> Mobile device, security key, smart card</li>
            <li><strong>Something you are:</strong> Biometrics (fingerprints, facial recognition)</li>
            <li><strong>Somewhere you are:</strong> Location-based verification</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Common MFA Methods:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Time-based One-Time Passwords (TOTP):</strong> Apps like Google Authenticator</li>
            <li><strong>SMS/Email Codes:</strong> One-time codes sent via message</li>
            <li><strong>Push Notifications:</strong> Approve/deny prompts on mobile devices</li>
            <li><strong>Hardware Tokens:</strong> YubiKey, security keys</li>
            <li><strong>Biometric Verification:</strong> Fingerprint, face, or voice recognition</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Implementation Best Practices:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Make MFA mandatory for all users, especially administrators</li>
            <li>Offer multiple MFA options for accessibility</li>
            <li>Implement secure fallback mechanisms</li>
            <li>Use phishing-resistant methods (WebAuthn/FIDO2)</li>
            <li>Educate users on the importance of MFA</li>
          </ul>
          <p className="mt-4">Remember that not all MFA methods are equally secure. SMS-based verification is vulnerable to SIM swapping attacks, while hardware security keys provide the strongest protection against phishing attacks.</p>
        </div>
      );
    },
  },
  {
    description: "Managing user sessions securely",
    title: "Session Management",
    src: "https://images.unsplash.com/photo-1464865885825-be7cd16fad8d?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    ctaText: "Learn",
    ctaLink: "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html",
    content: () => {
      return (
        <div>
          <p>
            Session management is the process of securely handling user sessions after successful authentication. Poor session management can lead to session hijacking, fixation, and other attacks.
          </p>
          <h4 className="font-bold mt-4 mb-2">Session Token Properties:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>High entropy (unpredictable, random)</li>
            <li>Sufficient length (at least 128 bits)</li>
            <li>Issued via secure HTTPS connections</li>
            <li>Stored securely in HTTP-only cookies</li>
            <li>Include proper expiration and rotation</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Secure Cookie Configuration:</h4>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// Example cookie configuration
Set-Cookie: sessionId=abc123; 
  HttpOnly;           // Prevents JavaScript access
  Secure;             // Only sent over HTTPS
  SameSite=Strict;    // Prevents CSRF
  Path=/;             // Restricts to specific paths
  Max-Age=3600;       // Session timeout in seconds
  Domain=example.com  // Restricts to specific domain`}
          </pre>
          <h4 className="font-bold mt-4 mb-2">Session Lifecycle Management:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Creation:</strong> Generate new session after login, avoid reusing IDs</li>
            <li><strong>Regeneration:</strong> Issue new session ID after privilege changes</li>
            <li><strong>Expiration:</strong> Implement idle and absolute timeouts</li>
            <li><strong>Termination:</strong> Properly invalidate sessions on logout</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Common Attacks:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Session Hijacking:</strong> Attacker steals a valid session token</li>
            <li><strong>Session Fixation:</strong> Attacker sets a known session ID before login</li>
            <li><strong>Cross-Site Request Forgery (CSRF):</strong> Tricks users into performing actions</li>
            <li><strong>Cross-Site Script Inclusion (XSSI):</strong> Leaks sensitive data from scripts</li>
          </ul>
        </div>
      );
    },
  },
  {
    description: "Defending access with authorization",
    title: "Access Control",
    src: "https://images.unsplash.com/photo-1582139329536-e7284fece509?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2080&q=80",
    ctaText: "Learn",
    ctaLink: "https://owasp.org/www-community/Access_Control",
    content: () => {
      return (
        <div>
          <p>
            Access control determines what authenticated users can do within a system. While authentication verifies who a user is, authorization controls what they can access.
          </p>
          <h4 className="font-bold mt-4 mb-2">Access Control Models:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Role-Based Access Control (RBAC):</strong> Permissions based on roles assigned to users</li>
            <li><strong>Attribute-Based Access Control (ABAC):</strong> Permissions based on user attributes, resource attributes, and environmental conditions</li>
            <li><strong>Discretionary Access Control (DAC):</strong> Resource owners determine access rights</li>
            <li><strong>Mandatory Access Control (MAC):</strong> System-enforced policy determines access</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Common Vulnerabilities:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Insecure Direct Object References:</strong> Exposing internal implementation objects to users</li>
            <li><strong>Missing Function Level Access Control:</strong> Not enforcing authorization at the function level</li>
            <li><strong>Horizontal Privilege Escalation:</strong> Accessing resources of another user at the same privilege level</li>
            <li><strong>Vertical Privilege Escalation:</strong> Gaining higher privileges than authorized</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Best Practices:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Implement the principle of least privilege</li>
            <li>Deny by default, then allow explicitly</li>
            <li>Enforce access control on the server side</li>
            <li>Centralize access control mechanisms</li>
            <li>Log all access control decisions and failures</li>
            <li>Regularly review and test access controls</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Example Implementation Pattern:</h4>
          <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-sm overflow-x-auto mt-2 text-xs">
{`// Example access control middleware
function checkPermission(requiredPermission) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    if (!req.user.permissions.includes(requiredPermission)) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    next(); // User has permission, continue
  };
}

// Usage in route definition
app.get('/admin/users', 
  checkPermission('ADMIN_VIEW_USERS'), 
  adminController.getUsers
);`}
          </pre>
        </div>
      );
    },
  },
  {
    description: "Protecting authentication flows",
    title: "OAuth & OpenID Connect",
    src: "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2071&q=80",
    ctaText: "Learn",
    ctaLink: "https://oauth.net/2/",
    content: () => {
      return (
        <div>
          <p>
            OAuth 2.0 and OpenID Connect (OIDC) are industry-standard protocols for authorization and authentication that allow applications to securely access resources on behalf of users without sharing passwords.
          </p>
          <h4 className="font-bold mt-4 mb-2">Key Concepts:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>OAuth 2.0:</strong> Authorization framework that enables third-party applications to access resources</li>
            <li><strong>OpenID Connect:</strong> Identity layer on top of OAuth 2.0 for authentication</li>
            <li><strong>Authorization Server:</strong> Issues access tokens to clients</li>
            <li><strong>Resource Server:</strong> Hosts protected resources</li>
            <li><strong>Client:</strong> Application requesting access to resources</li>
            <li><strong>Resource Owner:</strong> User who authorizes access</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">OAuth 2.0 Grant Types:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li><strong>Authorization Code:</strong> Server-side apps, most secure flow</li>
            <li><strong>PKCE (Proof Key for Code Exchange):</strong> Enhanced security for public clients</li>
            <li><strong>Client Credentials:</strong> Machine-to-machine communication</li>
            <li><strong>Resource Owner Password Credentials:</strong> Direct user credentials (legacy, avoid when possible)</li>
            <li><strong>Implicit Flow:</strong> Deprecated due to security concerns</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Security Best Practices:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Always use HTTPS for all OAuth/OIDC endpoints</li>
            <li>Implement state parameter to prevent CSRF attacks</li>
            <li>Use PKCE for all authorization code flows</li>
            <li>Validate all tokens and parameters</li>
            <li>Use short-lived access tokens and refresh tokens</li>
            <li>Implement proper token storage mechanisms</li>
            <li>Register redirect URIs exactly</li>
          </ul>
          <h4 className="font-bold mt-4 mb-2">Common Vulnerabilities:</h4>
          <ul className="list-disc pl-5 space-y-1 mt-2">
            <li>Insecure redirect URIs</li>
            <li>Missing state parameter</li>
            <li>Token leakage via browser history or logs</li>
            <li>Cross-Site Request Forgery (CSRF)</li>
            <li>Insufficient token validation</li>
          </ul>
        </div>
      );
    },
  },
];