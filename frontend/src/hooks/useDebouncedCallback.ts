import { useCallback, useEffect, useRef } from "react";

export function useDebouncedCallback<T extends unknown[]>(
  callback: (...args: T) => void,
  delayMs: number,
) {
  const callbackRef = useRef(callback);
  const timerRef = useRef<number | undefined>();

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    return () => window.clearTimeout(timerRef.current);
  }, []);

  return useCallback(
    (...args: T) => {
      window.clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(() => callbackRef.current(...args), delayMs);
    },
    [delayMs],
  );
}
