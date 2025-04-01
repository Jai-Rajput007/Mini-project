'use client';

import * as React from 'react';

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success';
}

function Badge({
  className,
  variant = 'default',
  ...props
}: BadgeProps) {
  const variantClasses = {
    default: 'bg-purple-600 text-white hover:bg-purple-700',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-gray-800 dark:text-gray-50 dark:hover:bg-gray-700',
    destructive: 'bg-red-500 text-white hover:bg-red-600',
    outline: 'text-gray-900 border border-gray-200 hover:bg-gray-100 dark:border-gray-800 dark:text-gray-50 dark:hover:bg-gray-800',
    success: 'bg-green-500 text-white hover:bg-green-600',
  };

  return (
    <div
      className={`inline-flex items-center rounded-full border border-transparent px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${variantClasses[variant]} ${className}`}
      {...props}
    />
  );
}

export { Badge };
