import {
  CategoryScale,
  Chart,
  Filler,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { useTranslation } from 'react-i18next';

import { formatNumber } from '../../i18n/format';
import { ChartTable } from './ChartTable';
import { cssVar } from './colors';
import { axisNumber, chartChrome, withAlpha } from './theme';

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

interface LineChartProps {
  labels: string[];
  values: number[];
  label: string;
  /** CSS custom property with the line colour. */
  colorVar: string;
  testId?: string;
  /** How a value reads in the tooltip and in the table (the number by default). */
  formatValue?: (value: number, index: number) => string;
  height?: number;
}

/**
 * Single-series trend: a 2px line over a light wash of its colour, ringed points, and a tooltip
 * for the whole column under the pointer. The values are also a table for screen readers.
 */
const LineChart = ({
  labels,
  values,
  label,
  colorVar,
  testId,
  formatValue,
  height = 220,
}: LineChartProps) => {
  const { i18n } = useTranslation();
  const chrome = chartChrome();
  const color = cssVar(colorVar);
  const format = formatValue ?? ((value: number) => formatNumber(value, i18n.language));

  return (
    <div data-testid={testId}>
      <div style={{ height }}>
        <Line
          role="img"
          aria-label={label}
          data={{
            labels,
            datasets: [
              {
                label,
                data: values,
                borderColor: color,
                backgroundColor: withAlpha(color, 0.1),
                fill: 'origin',
                borderWidth: 2,
                tension: 0.3,
                cubicInterpolationMode: 'monotone',
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: color,
                pointBorderColor: chrome.surface,
                pointBorderWidth: 2,
              },
            ],
          }}
          options={{
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: { label: (item) => format(Number(item.raw), item.dataIndex) },
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                grid: { color: chrome.grid },
                border: { display: false },
                ticks: {
                  color: chrome.text,
                  callback: (value) => axisNumber(Number(value), i18n.language),
                },
              },
              x: {
                grid: { display: false },
                border: { color: chrome.grid },
                ticks: { color: chrome.text, maxRotation: 0, autoSkipPadding: 12 },
              },
            },
          }}
        />
      </div>
      <ChartTable caption={label} labels={labels} values={values.map(format)} />
    </div>
  );
};

export default LineChart;
