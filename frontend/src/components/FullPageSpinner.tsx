import { IonSpinner } from '@ionic/react';
import { useTranslation } from 'react-i18next';

export const FullPageSpinner = () => {
  const { t } = useTranslation();
  return (
    <div
      style={{ display: 'grid', placeItems: 'center', height: '100vh' }}
      role="status"
      aria-label={t('common.loading')}
    >
      <IonSpinner name="crescent" />
    </div>
  );
};
