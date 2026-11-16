import { IonIcon, IonText } from '@ionic/react';
import { cloudOfflineOutline } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { useOnline, usePendingCount } from '../offline/useOnline';

/** Shown under the toolbar while there is no connection. */
export const OfflineBanner = () => {
  const { t } = useTranslation();
  const online = useOnline();
  const pending = usePendingCount();
  if (online) return null;
  return (
    <div className="offline-banner" role="status" data-testid="offline-banner">
      <IonIcon icon={cloudOfflineOutline} aria-hidden="true" />
      <IonText>
        {t('offline.banner')}
        {pending > 0 && <> {t('offline.pending', { count: pending })}</>}
      </IonText>
    </div>
  );
};
