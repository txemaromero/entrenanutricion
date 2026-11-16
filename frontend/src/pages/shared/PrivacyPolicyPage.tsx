import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import { homePath } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import { PRIVACY, PRIVACY_SECTIONS } from '../../privacy';

/** Public privacy policy (GDPR information duty), reachable before and after signing in. */
const PrivacyPolicyPage = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const values = {
    controller: PRIVACY.controller || t('privacy.controllerPlaceholder'),
    contact: PRIVACY.contact || t('privacy.contactPlaceholder'),
    days: PRIVACY.accountRetentionDays,
    backupDays: PRIVACY.backupRetentionDays,
  };

  return (
    <PageLayout title={t('privacy.title')} backHref={homePath(user)} narrow>
      <div className="stack" data-testid="privacy-policy">
        <p className="muted" style={{ margin: 0 }}>
          {t('privacy.version', { version: PRIVACY.version })}
        </p>
        <p>{t('privacy.intro')}</p>
        {PRIVACY_SECTIONS.map((key) => (
          <IonCard key={key}>
            <IonCardHeader>
              <IonCardTitle style={{ fontSize: '1.05rem' }}>
                {t(`privacy.sections.${key}.title`)}
              </IonCardTitle>
            </IonCardHeader>
            <IonCardContent>{t(`privacy.sections.${key}.body`, values)}</IonCardContent>
          </IonCard>
        ))}
      </div>
    </PageLayout>
  );
};

export default PrivacyPolicyPage;
