import { IonCard, IonCardContent, IonChip } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import type { Menu, Nutrients } from '../../api/types';
import { formatNumber } from '../../i18n/format';
import { formatGrams } from '../../utils/nutrition';

/** "1.234 / 1.700 kcal" and the macros of a meal or a day. */
export const NutrientsLine = ({ value, target }: { value: Nutrients; target?: Nutrients }) => {
  const { t, i18n } = useTranslation();
  const n = (number: number) => formatNumber(number, i18n.language, { maximumFractionDigits: 0 });
  return (
    <span className="muted">
      {target
        ? t('menu.kcalOfTarget', { kcal: n(value.calories), target: n(target.calories) })
        : t('menu.kcal', { kcal: n(value.calories) })}{' '}
      ·{' '}
      {t('nutrition.macroGrams', {
        proteins: n(value.proteinsG),
        carbs: n(value.carbsG),
        fats: n(value.fatsG),
      })}
    </span>
  );
};

/** Chip with the deviation of the menu's calories from the plan (green within ±10 %). */
export const DeviationChip = ({ pct }: { pct: number | null }) => {
  const { t, i18n } = useTranslation();
  if (pct === null) return null;
  const within = Math.abs(pct) <= 10;
  return (
    <IonChip color={within ? 'success' : 'warning'} data-testid="menu-deviation">
      {t(within ? 'menu.withinTarget' : 'menu.offTarget', {
        pct: formatNumber(pct, i18n.language, { signDisplay: 'exceptZero' }),
      })}
    </IonChip>
  );
};

/** Sample day menu, meal by meal, with the totals against the plan's targets. */
export const MenuView = ({
  menu,
  showDeviation = false,
}: {
  menu: Menu;
  showDeviation?: boolean;
}) => {
  const { t, i18n } = useTranslation();
  const n = (value: number) => formatNumber(value, i18n.language, { maximumFractionDigits: 0 });

  return (
    <div className="stack" data-testid="menu-view">
      <div className="row row--between row--wrap">
        <NutrientsLine value={menu.totals} target={menu.target} />
        {showDeviation && <DeviationChip pct={menu.caloriesDeviationPct} />}
      </div>
      {menu.meals
        .filter((meal) => meal.items.length > 0)
        .map((meal) => (
          <IonCard key={meal.meal} className="ion-no-margin" data-testid={`menu-meal-${meal.meal}`}>
            <IonCardContent className="stack" style={{ gap: 6 }}>
              <div className="row row--between row--wrap">
                <strong>{t(`enums.meal.${meal.meal}`)}</strong>
                <small className="muted">
                  {t('menu.kcalOfTarget', {
                    kcal: n(meal.totals.calories),
                    target: n(meal.target.calories),
                  })}
                </small>
              </div>
              <ul className="menu-items">
                {meal.items.map((item) => (
                  <li key={item.id} className="row row--between">
                    <span>{item.food.name}</span>
                    <span className="muted">
                      {formatGrams(item.grams, i18n.language)} ·{' '}
                      {t('menu.kcal', { kcal: n(item.calories) })}
                    </span>
                  </li>
                ))}
              </ul>
            </IonCardContent>
          </IonCard>
        ))}
    </div>
  );
};
