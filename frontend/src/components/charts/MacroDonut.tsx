import { ArcElement, Chart, Legend, Tooltip } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import { useTranslation } from 'react-i18next';

import type { Macros } from '../../api/types';
import { formatNumber } from '../../i18n/format';
import { cssVar } from './colors';

Chart.register(ArcElement, Tooltip, Legend);

const MACRO_KEYS = ['carbs', 'proteins', 'fats'] as const;

/** Donut of the share of kcal per macro (colours shared with the macro cards). */
const MacroDonut = ({ macros }: { macros: Macros }) => {
  const { t, i18n } = useTranslation();
  const labels = MACRO_KEYS.map(
    (key) => `${t(`enums.macro.${key}`)} (${formatNumber(macros[key].pct, i18n.language)} %)`,
  );
  return (
    <div style={{ maxWidth: 320, margin: '0 auto' }}>
      <Doughnut
        aria-label={t('nutrition.chartLabel')}
        role="img"
        data={{
          labels,
          datasets: [
            {
              data: MACRO_KEYS.map((key) => macros[key].kcal),
              backgroundColor: MACRO_KEYS.map((key) => cssVar(`--en-macro-${key}`)),
              borderWidth: 0,
            },
          ],
        }}
        options={{
          cutout: '62%',
          plugins: {
            legend: { position: 'bottom' },
            tooltip: { callbacks: { label: (item) => `${item.label}: ${item.raw} kcal` } },
          },
        }}
      />
    </div>
  );
};

export default MacroDonut;
