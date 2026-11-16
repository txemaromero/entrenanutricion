import {
  IonAvatar,
  IonBackButton,
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonIcon,
  IonPage,
  IonRefresher,
  IonRefresherContent,
  IonTitle,
  IonToolbar,
  type RefresherEventDetail,
} from '@ionic/react';
import { personCircleOutline } from 'ionicons/icons';
import { forwardRef, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../auth/useAuth';
import { PATHS } from '../auth/routing';
import { LanguageMenu } from './LanguageMenu';
import { EmailVerificationBanner } from './EmailVerificationBanner';
import { OfflineBanner } from './OfflineBanner';

interface PageLayoutProps {
  title: string;
  children: ReactNode;
  /** Shows a back button that falls back to this route. */
  backHref?: string;
  /** Extra buttons placed before the language selector. */
  actions?: ReactNode;
  /** Second sticky toolbar under the title (segments, search…). */
  subHeader?: ReactNode;
  /** Enables pull-to-refresh. */
  onRefresh?: () => Promise<unknown>;
  narrow?: boolean;
  /** Content after the main container (FAB buttons, modals). */
  overlay?: ReactNode;
  /** Hide the "confirm your email" reminder (the verification page itself). */
  hideEmailReminder?: boolean;
}

/** Fixed top bar (title + language selector, avatar for admins) and centred content. */
export const PageLayout = forwardRef<HTMLIonContentElement, PageLayoutProps>(
  (
    {
      title,
      children,
      backHref,
      actions,
      subHeader,
      onRefresh,
      narrow,
      overlay,
      hideEmailReminder,
    },
    contentRef,
  ) => {
    const { t } = useTranslation();
    const { user } = useAuth();

    const refresh = async (event: CustomEvent<RefresherEventDetail>) => {
      try {
        await onRefresh?.();
      } finally {
        event.detail.complete();
      }
    };

    return (
      <IonPage>
        <IonHeader>
          <IonToolbar>
            {backHref && (
              <IonButtons slot="start">
                <IonBackButton defaultHref={backHref} text={t('common.back')} />
              </IonButtons>
            )}
            <IonTitle>{title}</IonTitle>
            <IonButtons slot="end">
              {actions}
              <LanguageMenu />
              {user?.role === 'admin' && (
                <IonButton
                  routerLink={PATHS.profile}
                  className="icon-button"
                  aria-label={t('layout.openProfile')}
                  data-testid="admin-profile-button"
                >
                  {user.profilePhotoUrl ? (
                    <IonAvatar style={{ width: 28, height: 28 }}>
                      <img src={user.profilePhotoUrl} alt="" />
                    </IonAvatar>
                  ) : (
                    <IonIcon slot="icon-only" icon={personCircleOutline} aria-hidden="true" />
                  )}
                </IonButton>
              )}
            </IonButtons>
          </IonToolbar>
          {subHeader && <IonToolbar className="sticky-segment">{subHeader}</IonToolbar>}
          <OfflineBanner />
        </IonHeader>
        <IonContent ref={contentRef}>
          {onRefresh && (
            <IonRefresher slot="fixed" onIonRefresh={refresh}>
              <IonRefresherContent />
            </IonRefresher>
          )}
          {/* Focusable region: lets keyboard users scroll pages without interactive content. */}
          <div
            className={narrow ? 'page-container page-container--narrow' : 'page-container'}
            role="region"
            aria-label={title}
            tabIndex={0}
          >
            {!hideEmailReminder && <EmailVerificationBanner />}
            {children}
          </div>
          {overlay}
        </IonContent>
      </IonPage>
    );
  },
);

PageLayout.displayName = 'PageLayout';
