import { IonButton, IonItem, IonLabel, IonList, IonPopover } from '@ionic/react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { Language } from '../i18n';
import { useLanguage } from '../i18n/useLanguage';
import { Flag } from './Flag';

/** Top-right language selector: current flag opens a list with ES / EN / CA. */
export const LanguageMenu = () => {
  const { t } = useTranslation();
  const { language, languages, changeLanguage } = useLanguage();
  const [anchor, setAnchor] = useState<Event>();

  const select = async (next: Language) => {
    setAnchor(undefined);
    await changeLanguage(next);
  };

  return (
    <>
      <IonButton
        className="icon-button"
        aria-label={t('language.change')}
        aria-haspopup="menu"
        aria-expanded={anchor ? true : undefined}
        onClick={(event) => setAnchor(event.nativeEvent)}
        data-testid="language-menu"
      >
        <Flag language={language} />
      </IonButton>
      <IonPopover isOpen={Boolean(anchor)} event={anchor} onDidDismiss={() => setAnchor(undefined)}>
        <IonList lines="none" aria-label={t('language.change')}>
          {languages.map((option) => (
            <IonItem
              key={option}
              button
              detail={false}
              onClick={() => void select(option)}
              aria-current={option === language ? 'true' : undefined}
              data-testid={`language-option-${option}`}
            >
              <span slot="start">
                <Flag language={option} />
              </span>
              <IonLabel>{t(`language.${option}`)}</IonLabel>
            </IonItem>
          ))}
        </IonList>
      </IonPopover>
    </>
  );
};
