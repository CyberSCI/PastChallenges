import { useWritable } from '$lib/hooks/use-shared-stores';

export const useAuthenticated = () => useWritable('authenticated', false);
