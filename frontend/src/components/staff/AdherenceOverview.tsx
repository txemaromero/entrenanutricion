import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';
import {
  alertCircleOutline,
  analyticsOutline,
  checkmarkCircleOutline,
  peopleOutline,
} from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import type { AdherenceList, AdherenceStatus } from '../../api/types';
import { formatNumber } from '../../i18n/format';
import { BarChart, DonutChart } from '../charts';
import { StatTiles } from '../StatTiles';
import { ADHERENCE_COLOR_VARS } from './adherenceColors';

/** The whole list at a glance: figures, clients per status and per band of adherence. */
export const AdherenceOverview = ({ data }: { data: AdherenceList }) => {
  const { t, i18n } = useTranslation();
  const count = (status: AdherenceStatus) =>
    data.counts.find((entry) => entry.status === status)?.count ?? 0;
  const total = data.counts.reduce((sum, entry) => sum + entry.count, 0);
  const n = (value: number) => formatNumber(value, i18n.language);

  return (
    <div className="stack" data-testid="adherence-overview">
      <StatTiles
        items={[
          {
            key: 'average',
            icon: analyticsOutline,
            label: t('adherence.overview.average'),
            value:
              data.averagePercent === null
                ? '—'
                : t('adherence.overview.percentValue', { value: n(data.averagePercent) }),
          },
          {
            key: 'clients',
            icon: peopleOutline,
            label: t('adherence.overview.clients'),
            value: n(total),
          },
          {
            key: 'on-track',
            icon: checkmarkCircleOutline,
            label: t('enums.adherenceStatus.on_track'),
            value: n(count('on_track')),
          },
          {
            key: 'need-help',
            icon: alertCircleOutline,
            label: t('adherence.overview.needHelp'),
            value: n(count('inactive') + count('at_risk')),
          },
        ]}
      />
      {total > 0 && (
        <div className="card-grid">
          <IonCard>
            <IonCardHeader>
              <IonCardTitle style={{ fontSize: '1.05rem' }}>
                {t('adherence.overview.byStatus')}
              </IonCardTitle>
            </IonCardHeader>
            <IonCardContent>
              <DonutChart
                testId="adherence-donut"
                labels={data.counts.map((entry) => t(`enums.adherenceStatus.${entry.status}`))}
                values={data.counts.map((entry) => entry.count)}
                colorVars={data.counts.map((entry) => ADHERENCE_COLOR_VARS[entry.status])}
                label={t('adherence.overview.byStatus')}
                centre={
                  <>
                    <strong>{n(total)}</strong>
                    <small>{t('adherence.overview.clientsShort', { count: total })}</small>
                  </>
                }
              />
            </IonCardContent>
          </IonCard>
          <IonCard>
            <IonCardHeader>
              <IonCardTitle style={{ fontSize: '1.05rem' }}>
                {t('adherence.overview.byBand')}
              </IonCardTitle>
            </IonCardHeader>
            <IonCardContent>
              <BarChart
                testId="adherence-distribution"
                height={200}
                labels={data.distribution.map((band) =>
                  t('adherence.overview.band', { low: band.low, high: band.high }),
                )}
                values={data.distribution.map((band) => band.count)}
                label={t('adherence.overview.byBand')}
                colorVar="--ion-color-primary"
                formatValue={(value) => t('adherence.overview.clientsCount', { count: value })}
              />
            </IonCardContent>
          </IonCard>
        </div>
      )}
    </div>
  );
};
