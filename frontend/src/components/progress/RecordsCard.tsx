import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import { trainingApi } from '../../api/client-features';
import { useResource } from '../../hooks/useResource';
import { formatDate, formatNumber } from '../../i18n/format';

/** Progress › Workout: heaviest set and estimated 1RM of every weighted exercise. */
export const RecordsCard = () => {
  const { t, i18n } = useTranslation();
  const { data } = useResource(trainingApi.records);
  if (!data) return null;
  const kg = (value: number) => formatNumber(value, i18n.language);

  return (
    <IonCard data-testid="records-card">
      <IonCardHeader>
        <IonCardTitle style={{ fontSize: '1.1rem' }}>{t('records.title')}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent>
        {data.length === 0 ? (
          <p className="muted" style={{ margin: 0 }}>
            {t('records.empty')}
          </p>
        ) : (
          <ul className="stack" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {data.map((record) => (
              <li
                key={record.exercise.id}
                className="row row--between row--wrap"
                data-testid={`record-${record.exercise.id}`}
              >
                <span>
                  <strong style={{ display: 'block' }}>{record.exercise.name}</strong>
                  <small className="muted">
                    {formatDate(record.bestWeightDate, i18n.language)} ·{' '}
                    {t('records.oneRm', { weight: kg(record.estimatedOneRmKg) })}
                  </small>
                </span>
                <strong>
                  {t('records.best', {
                    weight: kg(record.bestWeightKg),
                    reps: record.bestWeightReps,
                  })}
                </strong>
              </li>
            ))}
          </ul>
        )}
        {data.length > 0 && (
          <p className="muted" style={{ marginBottom: 0 }}>
            <small>{t('records.oneRmHelp')}</small>
          </p>
        )}
      </IonCardContent>
    </IonCard>
  );
};
