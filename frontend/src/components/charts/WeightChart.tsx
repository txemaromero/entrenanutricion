import {
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useTranslation } from 'react-i18next';

import type { WeightSummary } from '../../api/types';
import { formatDate } from '../../i18n/format';
import { cssVar } from './colors';

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

/**
 * Weight evolution with horizontal lines for the initial and target weights.
 * Re-renders from props, so a new record shows up immediately (regression #7).
 */
const WeightChart = ({
  summary,
  compact = false,
}: {
  summary: WeightSummary;
  compact?: boolean;
}) => {
  const { t, i18n } = useTranslation();
  const labels = summary.records.map((record) =>
    formatDate(record.date, i18n.language, { day: '2-digit', month: 'short' }),
  );
  const flat = (value: number) => summary.records.map(() => value);

  return (
    <div
      style={{ height: compact ? 180 : 280 }}
      data-testid="weight-chart"
      data-points={summary.records.length}
    >
      <Line
        role="img"
        aria-label={t('progress.weightChartLabel')}
        data={{
          labels,
          datasets: [
            {
              label: t('progress.weight'),
              data: summary.records.map((record) => record.weightKg),
              borderColor: cssVar('--ion-color-primary'),
              backgroundColor: cssVar('--ion-color-primary'),
              tension: 0.25,
            },
            {
              label: t('progress.initialWeight'),
              data: flat(summary.initialWeightKg),
              borderColor: cssVar('--ion-color-medium'),
              borderDash: [6, 6],
              pointRadius: 0,
            },
            {
              label: t('progress.targetWeight'),
              data: flat(summary.targetWeightKg),
              borderColor: cssVar('--ion-color-tertiary'),
              borderDash: [4, 4],
              pointRadius: 0,
            },
          ],
        }}
        options={{
          maintainAspectRatio: false,
          plugins: { legend: { display: !compact, position: 'bottom' } },
          scales: { y: { title: { display: !compact, text: t('common.kg') } } },
        }}
      />
    </div>
  );
};

export default WeightChart;
