import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge conditional class lists, resolving conflicting Tailwind utilities last-wins. */
export function cn(...inputs) {
	return twMerge(clsx(inputs));
}
