"use client";
import React, { useState } from "react";
import { motion } from "framer-motion";
import { AlertCircle, CheckCircle, Copy, ExternalLink } from "lucide-react";

interface LinkCheckerFormProps {
  className?: string;
}

export default function LinkCheckerForm({ className }: LinkCheckerFormProps) {
  const [url, setUrl] = useState("");
  const [isValidUrl, setIsValidUrl] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<null | {
    isSafe: boolean;
    score: number;
    details: string[];
  }>(null);
  const [copied, setCopied] = useState(false);

  const validateUrl = (input: string) => {
    try {
      new URL(input);
      return true;
    } catch (e) {
      return false;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    setUrl(input);
    
    if (input === "") {
      setIsValidUrl(true);
    } else {
      setIsValidUrl(validateUrl(input));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url || !isValidUrl) {
      return;
    }
    
    setIsLoading(true);
    
    // Simulate API call with a timeout
    setTimeout(() => {
      // Mock result - in a real app, this would come from an API
      const mockResult = {
        isSafe: url.includes('safex.com'), // Simple demo logic based on URL
        score: url.length > 10 ? 85 : 65, // Simple demo scoring
        details: [
          "Domain registration date: 2023-01-15",
          "SSL certificate: Valid",
          "Domain age: 3 months",
          "Suspicious URL patterns: None detected",
          "Known malicious patterns: None detected"
        ]
      };
      
      setResult(mockResult);
      setIsLoading(false);
    }, 2000);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const openInNewTab = () => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className={`w-full max-w-3xl mx-auto ${className}`}>
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg overflow-hidden">
        <div className="p-6 md:p-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Check if a link is safe
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            Enter a URL to check if it's potentially malicious or a phishing attempt.
          </p>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <input
                type="text"
                value={url}
                onChange={handleInputChange}
                placeholder="https://example.com"
                className={`w-full px-4 py-3 rounded-lg border ${
                  isValidUrl 
                    ? "border-gray-300 dark:border-gray-700" 
                    : "border-red-500 dark:border-red-500"
                } bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary`}
              />
              {url && (
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex space-x-1">
                  <button
                    type="button"
                    onClick={copyToClipboard}
                    className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    title="Copy to clipboard"
                  >
                    <Copy size={16} />
                  </button>
                  {isValidUrl && (
                    <button
                      type="button"
                      onClick={openInNewTab}
                      className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      title="Open in new tab"
                    >
                      <ExternalLink size={16} />
                    </button>
                  )}
                </div>
              )}
            </div>
            
            {!isValidUrl && url !== "" && (
              <p className="text-red-500 text-sm flex items-center">
                <AlertCircle size={16} className="mr-1" />
                Please enter a valid URL including http:// or https://
              </p>
            )}
            
            <button
              type="submit"
              disabled={!url || !isValidUrl || isLoading}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                !url || !isValidUrl || isLoading
                  ? "bg-gray-300 text-gray-500 dark:bg-gray-700 dark:text-gray-400 cursor-not-allowed"
                  : "bg-primary text-white hover:bg-primary/90"
              }`}
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Analyzing...
                </span>
              ) : (
                "Check Link"
              )}
            </button>
          </form>
          
          {copied && (
            <div className="mt-2 text-sm text-green-600 dark:text-green-400 flex items-center">
              <CheckCircle size={16} className="mr-1" />
              URL copied to clipboard
            </div>
          )}
          
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-8 border-t border-gray-200 dark:border-gray-800 pt-6"
            >
              <div className="flex items-center mb-4">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                  result.isSafe 
                    ? "bg-green-100 dark:bg-green-900" 
                    : "bg-red-100 dark:bg-red-900"
                }`}>
                  {result.isSafe ? (
                    <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                  ) : (
                    <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                  )}
                </div>
                <div className="ml-4">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                    {result.isSafe ? "Link appears safe" : "Potentially dangerous link"}
                  </h3>
                  <p className={`text-sm ${
                    result.isSafe 
                      ? "text-green-600 dark:text-green-400" 
                      : "text-red-600 dark:text-red-400"
                  }`}>
                    Safety score: {result.score}/100
                  </p>
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Analysis details:</h4>
                <ul className="space-y-2">
                  {result.details.map((detail, index) => (
                    <li key={index} className="text-sm text-gray-600 dark:text-gray-300 flex items-start">
                      <span className="mr-2">•</span>
                      {detail}
                    </li>
                  ))}
                </ul>
              </div>
              
              {!result.isSafe && (
                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-800">
                  <p className="text-sm text-red-800 dark:text-red-300">
                    <strong>Warning:</strong> This link shows characteristics commonly associated with phishing or malicious websites. 
                    We recommend not visiting this site or sharing any personal information.
                  </p>
                </div>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
} 