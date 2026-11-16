import {
  IonButton,
  IonCard,
  IonCardContent,
  IonContent,
  IonFooter,
  IonHeader,
  IonModal,
  IonTitle,
  IonToolbar,
} from '@ionic/react';
import { useTranslation } from 'react-i18next';

import type { Exercise } from '../../api/types';

const Section = ({ title, text }: { title: string; text: string }) =>
  text ? (
    <section>
      <h3 className="section-title">{title}</h3>
      <p>{text}</p>
    </section>
  ) : null;

/** "Exercise information" modal (US-13). */
export const ExerciseInfoModal = ({
  exercise,
  isOpen,
  onClose,
}: {
  exercise: Exercise;
  isOpen: boolean;
  onClose: () => void;
}) => {
  const { t } = useTranslation();
  return (
    <IonModal isOpen={isOpen} onDidDismiss={onClose} data-testid="exercise-info-modal">
      <IonHeader>
        <IonToolbar>
          <IonTitle>{t('exercise.infoTitle')}</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <h2 style={{ marginTop: 0 }}>{exercise.name}</h2>
        <Section title={t('exercise.description')} text={exercise.description} />
        {exercise.steps.length > 0 && (
          <section>
            <h3 className="section-title">{t('exercise.steps')}</h3>
            <ol className="stack" style={{ listStyle: 'none', padding: 0 }}>
              {exercise.steps.map((step, index) => (
                <li key={index}>
                  <IonCard>
                    <IonCardContent className="row" style={{ alignItems: 'flex-start' }}>
                      <strong aria-hidden="true" style={{ color: 'var(--ion-color-primary)' }}>
                        {index + 1}.
                      </strong>
                      <span>{step}</span>
                    </IonCardContent>
                  </IonCard>
                </li>
              ))}
            </ol>
          </section>
        )}
        <Section title={t('exercise.technique')} text={exercise.technique} />
        <Section title={t('exercise.commonMistakes')} text={exercise.commonMistakes} />
        <Section title={t('exercise.benefits')} text={exercise.benefits} />
      </IonContent>
      <IonFooter>
        <IonToolbar>
          <IonButton
            expand="block"
            onClick={onClose}
            data-testid="exercise-info-close"
            style={{ margin: 8 }}
          >
            {t('common.close')}
          </IonButton>
        </IonToolbar>
      </IonFooter>
    </IonModal>
  );
};
