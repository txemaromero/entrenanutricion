import { IonCard, IonCardContent } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import type { Macros, MealRow } from '../../api/types';
import { formatNumber } from '../../i18n/format';
import { MacroDonut } from '../charts';

const MACROS = ['carbs', 'proteins', 'fats'] as const;

/** Three macro cards (grams + kcal), donut with percentages and, for plans, the meal split. */
export const MacroBreakdown = ({ macros, meals }: { macros: Macros; meals?: MealRow[] }) => {
  const { t, i18n } = useTranslation();
  const n = (value: number) => formatNumber(value, i18n.language);

  return (
    <div className="stack">
      <div className="card-grid" style={{ gridTemplateColumns: 'repeat(3, minmax(0, 1fr))' }}>
        {MACROS.map((key) => (
          <IonCard
            key={key}
            className="macro-card"
            style={{ '--macro-color': `var(--en-macro-${key})` } as React.CSSProperties}
            data-testid={`macro-card-${key}`}
          >
            <IonCardContent style={{ padding: 10, textAlign: 'center' }}>
              <div className="muted" style={{ fontSize: '0.8rem' }}>
                {t(`enums.macro.${key}`)}
              </div>
              <strong style={{ fontSize: '1.3rem', display: 'block' }}>
                {n(macros[key].grams)} g
              </strong>
              <small>
                {n(macros[key].kcal)} {t('common.kcal')}
              </small>
            </IonCardContent>
          </IonCard>
        ))}
      </div>

      <IonCard>
        <IonCardContent>
          <MacroDonut macros={macros} />
        </IonCardContent>
      </IonCard>

      {meals && meals.length > 0 && (
        <>
          <h2 className="section-title">{t('nutrition.mealSplit')}</h2>
          <IonCard>
            <IonCardContent>
              <table className="data-table" data-testid="meal-table">
                <thead>
                  <tr>
                    <th scope="col">{t('nutrition.meal')}</th>
                    <th scope="col">%</th>
                    <th scope="col">{t('common.kcal')}</th>
                    <th scope="col">{t('nutrition.macrosShort')}</th>
                  </tr>
                </thead>
                <tbody>
                  {meals.map((row) => (
                    <tr key={row.meal}>
                      <th scope="row">{t(`enums.meal.${row.meal}`)}</th>
                      <td>{n(row.pct)} %</td>
                      <td>{n(row.kcal)}</td>
                      <td className="muted">
                        {t('nutrition.macroGrams', {
                          proteins: n(row.proteinsG),
                          carbs: n(row.carbsG),
                          fats: n(row.fatsG),
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </IonCardContent>
          </IonCard>
        </>
      )}
    </div>
  );
};
