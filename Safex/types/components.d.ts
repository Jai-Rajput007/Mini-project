declare module '@/components/ui/use-toast' {
  export interface ToastProps {
    title?: React.ReactNode;
    description?: React.ReactNode;
    action?: React.ReactElement;
    variant?: 'default' | 'destructive' | 'success';
    id?: string;
    onOpenChange?: (open: boolean) => void;
  }

  export function toast(props: Omit<ToastProps, 'id'>): {
    id: string;
    dismiss: () => void;
    update: (props: Omit<ToastProps, 'id'>) => void;
  };

  export function useToast(): {
    toast: typeof toast;
    dismiss: (toastId?: string) => void;
    toasts: ToastProps[];
  };

  export function Toaster(): JSX.Element;
}

declare module '@/components/ui/select' {
  import * as React from 'react';

  export interface SelectProps {
    value?: string;
    onValueChange?: (value: string) => void;
    disabled?: boolean;
    children?: React.ReactNode;
    defaultValue?: string;
  }

  export const Select: React.FC<SelectProps>;
  export const SelectGroup: React.FC<{ children?: React.ReactNode }>;
  export const SelectValue: React.FC<{ 
    placeholder?: string; 
    children?: React.ReactNode;
  }>;
  export const SelectTrigger: React.FC<{
    className?: string;
    children?: React.ReactNode;
  }>;
  export const SelectContent: React.FC<{
    className?: string;
    children?: React.ReactNode;
  }>;
  export const SelectLabel: React.FC<{
    className?: string;
    children?: React.ReactNode;
  }>;
  export const SelectItem: React.FC<{
    className?: string;
    children?: React.ReactNode;
    value: string;
  }>;
  export const SelectSeparator: React.FC<{
    className?: string;
  }>;
  export const SelectScrollUpButton: React.FC;
  export const SelectScrollDownButton: React.FC;
} 