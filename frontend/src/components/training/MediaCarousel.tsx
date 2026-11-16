import { IonButton, IonIcon } from '@ionic/react';
import { chevronBack, chevronForward } from 'ionicons/icons';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { ExerciseMedia } from '../../api/types';

/** Images and videos with arrows and native swipe (CSS scroll-snap). */
export const MediaCarousel = ({ media, title }: { media: ExerciseMedia[]; title: string }) => {
  const { t } = useTranslation();
  const track = useRef<HTMLDivElement>(null);
  const [index, setIndex] = useState(0);

  if (media.length === 0) return null;

  const go = (next: number) => {
    const target = Math.max(0, Math.min(media.length - 1, next));
    const element = track.current;
    if (element) element.scrollTo({ left: target * element.clientWidth, behavior: 'smooth' });
    setIndex(target);
  };

  const onScroll = () => {
    const element = track.current;
    if (element && element.clientWidth) {
      setIndex(Math.round(element.scrollLeft / element.clientWidth));
    }
  };

  return (
    <section
      className="carousel"
      aria-roledescription="carousel"
      aria-label={t('exercise.gallery', { name: title })}
      data-testid="media-carousel"
    >
      <div className="carousel-track" ref={track} onScroll={onScroll}>
        {media.map((item, position) => (
          <div
            key={item.id}
            className="carousel-slide"
            role="group"
            aria-roledescription="slide"
            aria-label={t('exercise.slide', { current: position + 1, total: media.length })}
          >
            {item.kind === 'video' ? (
              <video
                src={item.url}
                controls
                preload="metadata"
                aria-label={item.caption || title}
              />
            ) : (
              <img src={item.url} alt={item.caption || `${title} ${position + 1}`} loading="lazy" />
            )}
          </div>
        ))}
      </div>
      {media.length > 1 && (
        <>
          <IonButton
            className="carousel-arrow carousel-arrow--prev icon-button"
            onClick={() => go(index - 1)}
            disabled={index === 0}
            aria-label={t('exercise.previousMedia')}
          >
            <IonIcon slot="icon-only" icon={chevronBack} aria-hidden="true" />
          </IonButton>
          <IonButton
            className="carousel-arrow carousel-arrow--next icon-button"
            onClick={() => go(index + 1)}
            disabled={index === media.length - 1}
            aria-label={t('exercise.nextMedia')}
          >
            <IonIcon slot="icon-only" icon={chevronForward} aria-hidden="true" />
          </IonButton>
        </>
      )}
    </section>
  );
};
