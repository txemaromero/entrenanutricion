import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import { trainingApi } from '../../api/client-features';
import { useResource } from '../../hooks/useResource';
import { formatDate, formatNumber } from '../../i18n/format';
import { formatSets } from '../../utils/sets';
import { LoadChart } from '../charts';

const RECENT = 5;

/** "Your progress" on the exercise screen: record, top load per session and the last sessions. */
export const ExerciseProgress = ({ exerciseId, name }: { exerciseId: number; name: string }) => {
  const { t, i18n } = useTranslation();
  const { data } = useResource(() => trainingApi.exerciseHistory(exerciseId), [exerciseId]);
  if (!data) return null;
  const kg = (value: number) => formatNumber(value, i18n.language);
  const weighted = data.entries.filter((entry) => entry.maxWeightKg !== null).length;

  return (
    <IonCard data-testid="exercise-progress">
      <IonCardHeader>
        <IonCardTitle style={{ fontSize: '1.1rem' }}>{t('records.progressTitle')}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent className="stack">
        {data.entries.length === 0 && (
          <p className="muted" style={{ margin: 0 }}>
            {t('records.noHistory')}
          </p>
        )}
        {data.record && (
          <p style={{ margin: 0 }} data-testid="exercise-record">
            <strong>
              {t('records.best', {
                weight: kg(data.record.bestWeightKg),
                reps: data.record.bestWeightReps,
              })}
            </strong>{' '}
            · {formatDate(data.record.bestWeightDate, i18n.language)}
            <br />
            <small className="muted">
              {t('records.oneRm', { weight: kg(data.record.estimatedOneRmKg) })}
            </small>
          </p>
        )}
        {weighted >= 2 && <LoadChart name={name} entries={data.entries} />}
        {data.entries.length > 0 && (
          <ul
            className="stack"
            style={{ listStyle: 'none', padding: 0, margin: 0, gap: 4 }}
            data-testid="exercise-history"
          >
            {data.entries.slice(0, RECENT).map((entry, index) => (
              <li key={`${entry.date}-${index}`} className="row row--between row--wrap">
                <span className="muted">{formatDate(entry.date, i18n.language)}</span>
                <span>{formatSets(t, entry.sets, i18n.language)}</span>
              </li>
            ))}
          </ul>
        )}
      </IonCardContent>
    </IonCard>
  );
};
