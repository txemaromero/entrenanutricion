import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardSubtitle,
  IonCardTitle,
  IonIcon,
  IonProgressBar,
} from '@ionic/react';
import {
  barbellOutline,
  calendarOutline,
  flagOutline,
  flameOutline,
  footstepsOutline,
  ribbonOutline,
  scaleOutline,
  trophyOutline,
} from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { progressApi } from '../../api/client-features';
import type { Badge, BadgeCode } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { useResource } from '../../hooks/useResource';
import { formatDate } from '../../i18n/format';

const BADGE_ICONS: Record<BadgeCode, string> = {
  first_workout: footstepsOutline,
  workouts_10: flameOutline,
  workouts_50: barbellOutline,
  workouts_100: trophyOutline,
  perfect_week: calendarOutline,
  first_cycle: ribbonOutline,
  weight_logs_10: scaleOutline,
  goal_reached: flagOutline,
};

/** Every badge: earned ones with their date, pending ones with a progress bar. */
export const BadgeGrid = ({ badges }: { badges: Badge[] }) => {
  const { t, i18n } = useTranslation();
  return (
    <ul className="badge-grid">
      {badges.map((badge) => {
        const progress = t('badges.progress', { current: badge.current, target: badge.target });
        return (
          <li
            key={badge.code}
            className={`badge-card${badge.earned ? ' badge-card--earned' : ''}`}
            data-testid={`badge-${badge.code}`}
            data-earned={badge.earned}
          >
            <IonIcon
              icon={BADGE_ICONS[badge.code]}
              className="badge-card__icon"
              aria-hidden="true"
            />
            <strong>{t(`badges.items.${badge.code}.name`)}</strong>
            <small>{t(`badges.items.${badge.code}.description`)}</small>
            {badge.earned && badge.awardedAt ? (
              <small className="badge-card__status">
                {t('badges.earnedOn', { date: formatDate(badge.awardedAt, i18n.language) })}
              </small>
            ) : (
              <>
                <IonProgressBar
                  value={badge.target ? badge.current / badge.target : 0}
                  aria-label={`${t(`badges.items.${badge.code}.name`)}: ${progress}`}
                />
                <small className="badge-card__status">
                  {t('badges.pending')} · {progress}
                </small>
              </>
            )}
          </li>
        );
      })}
    </ul>
  );
};

/** Progress › Control: earned / total badges and a link to all of them. */
export const BadgesSummaryCard = () => {
  const { t } = useTranslation();
  const { data } = useResource(progressApi.badges);
  if (!data) return null;
  const earned = data.badges.filter((badge) => badge.earned);

  return (
    <IonCard data-testid="badges-summary">
      <IonCardHeader>
        <IonCardSubtitle>{t('badges.title')}</IonCardSubtitle>
        <IonCardTitle style={{ fontSize: '1.1rem' }}>
          {t('badges.summary', { earned: data.earnedCount, total: data.total })}
        </IonCardTitle>
      </IonCardHeader>
      <IonCardContent className="row row--between row--wrap">
        <span className="badge-strip" aria-hidden="true">
          {earned.map((badge) => (
            <IonIcon key={badge.code} icon={BADGE_ICONS[badge.code]} color="primary" />
          ))}
        </span>
        <IonButton size="small" fill="outline" routerLink={PATHS.badges} data-testid="badges-view">
          {t('badges.view')}
        </IonButton>
      </IonCardContent>
    </IonCard>
  );
};
