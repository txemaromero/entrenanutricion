import { IonButton, IonContent, IonPage } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import { PATHS } from '../../auth/routing';
import { AppLogo, HeroIllustration } from '../../components/Brand';
import { LanguageMenu } from '../../components/LanguageMenu';

const WelcomePage = () => {
  const { t } = useTranslation();
  return (
    <IonPage>
      <IonContent className="ion-padding">
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <LanguageMenu />
        </div>
        <div
          className="page-container page-container--narrow stack"
          style={{ textAlign: 'center' }}
        >
          <AppLogo size={72} />
          <h1 style={{ margin: 0 }}>{t('auth.welcome.title')}</h1>
          <HeroIllustration />
          <p className="muted">{t('auth.welcome.subtitle')}</p>
          <IonButton expand="block" routerLink={PATHS.register} data-testid="welcome-register">
            {t('auth.welcome.register')}
          </IonButton>
          <IonButton
            expand="block"
            fill="outline"
            routerLink={PATHS.login}
            data-testid="welcome-login"
          >
            {t('auth.welcome.login')}
          </IonButton>
        </div>
      </IonContent>
    </IonPage>
  );
};

export default WelcomePage;
