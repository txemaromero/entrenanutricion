import { useIonToast } from '@ionic/react';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { ApiError } from '../api/errors';
import { errorMessage } from '../utils/errors';
import { useConfirm } from './useConfirm';

/** Confirm, delete, report and refresh. Business conflicts (e.g. workout in use) are explained. */
export const useDeleteAction = () => {
  const { t } = useTranslation();
  const confirm = useConfirm();
  const [toast] = useIonToast();

  return useCallback(
    async ({
      name,
      remove,
      onDone,
    }: {
      name: string;
      remove: () => Promise<unknown>;
      onDone: () => unknown;
    }) => {
      const accepted = await confirm({
        header: t('staff.deleteTitle'),
        message: t('staff.deleteMessage', { name }),
        confirmText: t('common.delete'),
        destructive: true,
      });
      if (!accepted) return false;
      try {
        await remove();
        void toast({ message: t('staff.deleted', { name }), duration: 2000, color: 'success' });
        await onDone();
        return true;
      } catch (error) {
        const plans =
          error instanceof ApiError && Array.isArray(error.extra.plans)
            ? (error.extra.plans as { name: string }[]).map((plan) => plan.name).join(', ')
            : '';
        const message =
          error instanceof ApiError && error.code === 'workout_in_use'
            ? t('errors.workout_in_use', { plans })
            : errorMessage(t, error);
        void toast({ message, duration: 4000, color: 'danger' });
        return false;
      }
    },
    [confirm, t, toast],
  );
};
