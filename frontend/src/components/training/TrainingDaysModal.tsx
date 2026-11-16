import {
  IonButton,
  IonContent,
  IonHeader,
  IonModal,
  IonText,
  IonTitle,
  IonToolbar,
  useIonToast,
} from '@ionic/react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { trainingApi } from '../../api/client-features';
import { weekdayLabel } from '../../i18n/format';
import { errorMessage } from '../../utils/errors';

const WEEKDAYS = [0, 1, 2, 3, 4, 5, 6];
/** Same limit as the weekly training days of the onboarding form. */
const MAX_TRAINING_DAYS = 6;

/**
 * Pick the weekdays to train on (phase 9). They replace the recommended calendar; the number of
 * chosen days becomes the weekly training days. Mount it with a new `key` each time it opens.
 */
export const TrainingDaysModal = ({
  isOpen,
  days,
  custom,
  onClose,
  onSaved,
}: {
  isOpen: boolean;
  days: number[];
  custom: boolean;
  onClose: () => void;
  onSaved: () => void;
}) => {
  const { t, i18n } = useTranslation();
  const [toast] = useIonToast();
  const [selected, setSelected] = useState(() => new Set(days));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<unknown>();

  const toggle = (day: number) =>
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(day)) next.delete(day);
      else next.add(day);
      return next;
    });

  const save = async (chosen: number[]) => {
    setSaving(true);
    setError(undefined);
    try {
      await trainingApi.setTrainingDays(chosen);
      void toast({ message: t('training.days.saved'), duration: 2000, color: 'success' });
      onSaved();
    } catch (failure) {
      setError(failure);
    } finally {
      setSaving(false);
    }
  };

  return (
    <IonModal isOpen={isOpen} onDidDismiss={onClose} data-testid="training-days-modal">
      <IonHeader>
        <IonToolbar>
          <IonTitle>{t('training.days.title')}</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <div className="stack">
          <p>{t('training.days.intro', { max: MAX_TRAINING_DAYS })}</p>
          <div className="weekday-picker" role="group" aria-label={t('training.days.title')}>
            {WEEKDAYS.map((day) => {
              const pressed = selected.has(day);
              return (
                <button
                  key={day}
                  type="button"
                  className="weekday-toggle"
                  aria-pressed={pressed}
                  aria-label={weekdayLabel(day, i18n.language)}
                  disabled={!pressed && selected.size >= MAX_TRAINING_DAYS}
                  onClick={() => toggle(day)}
                  data-testid={`weekday-${day}`}
                >
                  {weekdayLabel(day, i18n.language, 'short')}
                </button>
              );
            })}
          </div>
          <IonText color="medium" role="status">
            <p>{t('training.days.selected', { count: selected.size })}</p>
          </IonText>
          {Boolean(error) && (
            <IonText color="danger" role="alert">
              <p>{errorMessage(t, error)}</p>
            </IonText>
          )}
          <div className="form-actions">
            <IonButton color="danger" fill="outline" onClick={onClose}>
              {t('common.cancel')}
            </IonButton>
            <IonButton
              disabled={saving || selected.size === 0}
              onClick={() => void save([...selected].sort((a, b) => a - b))}
              data-testid="training-days-save"
            >
              {t('common.save')}
            </IonButton>
          </div>
          {custom && (
            <IonButton
              fill="clear"
              disabled={saving}
              onClick={() => void save([])}
              data-testid="training-days-default"
            >
              {t('training.days.useDefault')}
            </IonButton>
          )}
        </div>
      </IonContent>
    </IonModal>
  );
};
