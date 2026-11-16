import { IonCard, IonCardContent, IonCardHeader, IonCardTitle, IonChip } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import { adherenceApi } from '../../api/staff';
import type { AdherenceRow, AdherenceStatus } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { useResource } from '../../hooks/useResource';
import { formatDate, formatNumber } from '../../i18n/format';
import { BarChart } from '../charts';
import { ProgressRing } from '../ProgressRing';
import { ADHERENCE_COLOR_VARS } from './adherenceColors';
import { Avatar } from './UserProfileBlocks';

const ADHERENCE_COLORS: Record<AdherenceStatus, string> = {
  inactive: 'danger',
  at_risk: 'warning',
  on_track: 'success',
};

export const AdherenceStatusChip = ({ status }: { status: AdherenceStatus }) => {
  const { t } = useTranslation();
  return (
    <IonChip color={ADHERENCE_COLORS[status]} data-testid="adherence-status">
      {t(`enums.adherenceStatus.${status}`)}
    </IonChip>
  );
};

/** Ring and facts of a client's adherence: sessions, last session and weight change. */
const AdherenceFacts = ({ row, ringSize = 64 }: { row: AdherenceRow; ringSize?: number }) => {
  const { t, i18n } = useTranslation();
  const number = (value: number, signed = false) =>
    formatNumber(value, i18n.language, {
      maximumFractionDigits: 1,
      signDisplay: signed ? 'exceptZero' : 'auto',
    });

  return (
    <div className="row" style={{ alignItems: 'center', gap: 14 }}>
      {row.adherencePercent !== null && (
        <ProgressRing
          size={ringSize}
          ratio={row.adherencePercent / 100}
          colorVar={ADHERENCE_COLOR_VARS[row.status]}
          label={t('adherence.percent', { percent: row.adherencePercent })}
        >
          <strong>{row.adherencePercent}%</strong>
        </ProgressRing>
      )}
      <div className="stack" style={{ gap: 4, minWidth: 0 }}>
        {row.adherencePercent === null ? (
          <span className="muted">{t('adherence.nothingScheduled')}</span>
        ) : (
          <>
            <strong>{t('adherence.percent', { percent: row.adherencePercent })}</strong>
            <span className="muted">
              {t('adherence.sessions', { done: row.sessions, scheduled: row.scheduled })}
            </span>
          </>
        )}
        <small className="muted" data-testid="adherence-last-session">
          {row.daysSinceLastSession === null
            ? t('adherence.noSessions')
            : row.daysSinceLastSession === 0
              ? t('adherence.lastToday')
              : t('adherence.lastDaysAgo', { count: row.daysSinceLastSession })}
          {row.currentWeightKg !== null && (
            <>
              {' · '}
              {t('adherence.weight', { weight: number(row.currentWeightKg) })}
              {row.weightChangeKg !== null &&
                ` (${t('adherence.weightChange', { change: number(row.weightChangeKg, true) })})`}
            </>
          )}
        </small>
      </div>
    </div>
  );
};

/** One client in the adherence list; opens the user's profile. */
export const AdherenceCard = ({ row }: { row: AdherenceRow }) => (
  <IonCard
    button
    routerLink={`${PATHS.users}/${row.user.id}`}
    data-testid={`adherence-${row.user.id}`}
    data-status={row.status}
  >
    <IonCardContent className="stack">
      <div className="row row--between">
        <div className="row" style={{ minWidth: 0 }}>
          <Avatar user={row.user} size={40} />
          <span style={{ minWidth: 0 }}>
            <strong style={{ display: 'block' }}>{row.user.fullName}</strong>
            <small className="muted">{row.planName}</small>
          </span>
        </div>
        <AdherenceStatusChip status={row.status} />
      </div>
      <AdherenceFacts row={row} />
    </IonCardContent>
  </IonCard>
);

/** User profile (staff): adherence to the plan with the last four weeks. */
export const ClientAdherenceCard = ({ userId }: { userId: number }) => {
  const { t, i18n } = useTranslation();
  const { data } = useResource(() => adherenceApi.client(userId), [userId]);
  if (!data) return null;

  return (
    <IonCard data-testid="client-adherence" data-status={data.status}>
      <IonCardHeader>
        <div className="row row--between">
          <IonCardTitle style={{ fontSize: '1.1rem' }}>{t('adherence.cardTitle')}</IonCardTitle>
          <AdherenceStatusChip status={data.status} />
        </div>
      </IonCardHeader>
      <IonCardContent className="stack">
        <AdherenceFacts row={data} ringSize={88} />
        <strong>{t('adherence.weeksTitle')}</strong>
        <BarChart
          testId="adherence-weeks"
          height={180}
          labels={data.weeks.map((week) =>
            t('adherence.week', {
              date: formatDate(week.start, i18n.language, { day: 'numeric', month: 'short' }),
            }),
          )}
          values={data.weeks.map((week) => week.sessions)}
          label={t('adherence.weeksChart')}
          colorVar="--ion-color-primary"
          formatValue={(_, index) => {
            const week = data.weeks[index];
            return week.scheduled || week.sessions
              ? t('adherence.weekSessions', { done: week.sessions, scheduled: week.scheduled })
              : t('adherence.weekEmpty');
          }}
          rowTestId="adherence-week"
        />
      </IonCardContent>
    </IonCard>
  );
};
