import { useCallback, useEffect, useRef, useState } from 'react';

/** Countdown for the rest between sets. Uses an end timestamp so it never drifts. */
export const useRestTimer = (initialSeconds: number, onFinish?: () => void) => {
  const [remaining, setRemaining] = useState(initialSeconds);
  const [running, setRunning] = useState(false);
  const [finished, setFinished] = useState(false);
  const endAt = useRef<number | null>(null);
  const interval = useRef<ReturnType<typeof setInterval> | null>(null);
  const onFinishRef = useRef(onFinish);

  useEffect(() => {
    onFinishRef.current = onFinish;
  });

  const stopTicking = () => {
    if (interval.current) clearInterval(interval.current);
    interval.current = null;
  };

  const start = useCallback(() => {
    if (remaining <= 0) return;
    setFinished(false);
    endAt.current = Date.now() + remaining * 1000;
    setRunning(true);
    stopTicking();
    interval.current = setInterval(() => {
      const left = Math.max(0, Math.ceil(((endAt.current ?? 0) - Date.now()) / 1000));
      setRemaining(left);
      if (left === 0) {
        stopTicking();
        setRunning(false);
        setFinished(true);
        onFinishRef.current?.();
      }
    }, 250);
  }, [remaining]);

  const pause = useCallback(() => {
    stopTicking();
    setRunning(false);
  }, []);

  const reset = useCallback(() => {
    stopTicking();
    setRunning(false);
    setFinished(false);
    setRemaining(initialSeconds);
  }, [initialSeconds]);

  useEffect(() => stopTicking, []);

  return { remaining, running, finished, start, pause, reset };
};

export const formatClock = (seconds: number): string =>
  `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;

/** Vibration and a short beep when the device allows it. */
export const notifyRestFinished = () => {
  try {
    navigator.vibrate?.([200, 100, 200]);
  } catch {
    /* vibration not supported */
  }
  try {
    const AudioContextClass =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextClass) return;
    const context = new AudioContextClass();
    const oscillator = context.createOscillator();
    oscillator.frequency.value = 880;
    oscillator.connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.3);
  } catch {
    /* audio not available */
  }
};
