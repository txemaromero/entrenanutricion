import { useTranslation } from 'react-i18next';

import type { Motivation } from '../api/types';
import { motivationParams } from '../utils/training';

/** Motivational messages: the backend returns i18n keys + parameters. */
export const MotivationMessage = ({ motivation }: { motivation?: Motivation }) => {
  const { t, i18n } = useTranslation();
  if (!motivation) return null;
  const params = motivationParams(motivation, i18n.language);
  return (
    <div className="motivation" role="note" data-testid="motivation">
      {motivation.keys.map((key) => (
        <p key={key} style={{ margin: '4px 0' }}>
          {t(key, params)}
        </p>
      ))}
    </div>
  );
};
