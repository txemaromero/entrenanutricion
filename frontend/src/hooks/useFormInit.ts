import { useEffect, useRef } from 'react';

/**
 * Fill an edit form once per loaded entity. Later reloads of the same entity (Ionic refreshes the
 * data when the view is entered) must not overwrite what the user is typing.
 */
export const useFormInit = <T extends { id: number }, F>(
  data: T | null | undefined,
  reset: (values: F) => void,
  toForm: (data: T) => F,
) => {
  const initializedFor = useRef<number | null>(null);
  useEffect(() => {
    if (data && initializedFor.current !== data.id) {
      initializedFor.current = data.id;
      reset(toForm(data));
    }
  }, [data, reset, toForm]);
};
