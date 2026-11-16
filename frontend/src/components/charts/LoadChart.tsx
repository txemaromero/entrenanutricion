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

import type { ExerciseHistory } from '../../api/types';
import { formatDate } from '../../i18n/format';
import { cssVar } from './colors';

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

/** Top load of each session of one exercise, oldest first (sessions without load are skipped). */
const LoadChart = ({ name, entries }: { name: string; entries: ExerciseHistory['entries'] }) => {
  const { t, i18n } = useTranslation();
  const points = entries.filter((entry) => entry.maxWeightKg !== null).reverse();

  return (
    <div style={{ height: 200 }} data-testid="load-chart" data-points={points.length}>
      <Line
        role="img"
        aria-label={t('records.chartLabel', { name })}
        data={{
          labels: points.map((entry) =>
            formatDate(entry.date, i18n.language, { day: '2-digit', month: 'short' }),
          ),
          datasets: [
            {
              label: t('records.maxWeight'),
              data: points.map((entry) => entry.maxWeightKg),
              borderColor: cssVar('--ion-color-primary'),
              backgroundColor: cssVar('--ion-color-primary'),
              tension: 0.25,
            },
          ],
        }}
        options={{
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { title: { display: true, text: t('common.kg') } } },
        }}
      />
    </div>
  );
};

export default LoadChart;
