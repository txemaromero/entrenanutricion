import { IonButton, IonCard, IonCardContent, IonIcon, IonSkeletonText } from '@ionic/react';
import { alertCircleOutline, fileTrayOutline } from 'ionicons/icons';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import type { ApiError } from '../api/errors';
import { errorMessage } from '../utils/errors';

const centered: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  textAlign: 'center',
  gap: 8,
  padding: '32px 16px',
};

export const EmptyState = ({
  title,
  message,
  action,
}: {
  title?: string;
  message?: string;
  action?: ReactNode;
}) => {
  const { t } = useTranslation();
  return (
    <div style={centered} role="status" data-testid="empty-state">
      <IonIcon icon={fileTrayOutline} style={{ fontSize: 48 }} color="medium" aria-hidden="true" />
      <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{title ?? t('states.emptyTitle')}</h2>
      {message && <p className="muted">{message}</p>}
      {action}
    </div>
  );
};

export const ErrorState = ({ error, onRetry }: { error: ApiError; onRetry?: () => void }) => {
  const { t } = useTranslation();
  return (
    <div style={centered} role="alert" data-testid="error-state">
      <IonIcon
        icon={alertCircleOutline}
        style={{ fontSize: 48 }}
        color="danger"
        aria-hidden="true"
      />
      <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{t('states.errorTitle')}</h2>
      <p className="muted">{errorMessage(t, error)}</p>
      {onRetry && (
        <IonButton fill="outline" onClick={onRetry}>
          {t('common.retry')}
        </IonButton>
      )}
    </div>
  );
};

export const ListSkeleton = ({ rows = 3 }: { rows?: number }) => {
  const { t } = useTranslation();
  return (
    <div className="stack" role="status" aria-busy="true" aria-label={t('states.loading')}>
      {Array.from({ length: rows }, (_, index) => (
        <IonCard key={index}>
          <IonCardContent>
            <IonSkeletonText animated style={{ width: '60%', height: 18 }} />
            <IonSkeletonText animated style={{ width: '90%' }} />
            <IonSkeletonText animated style={{ width: '40%' }} />
          </IonCardContent>
        </IonCard>
      ))}
    </div>
  );
};
