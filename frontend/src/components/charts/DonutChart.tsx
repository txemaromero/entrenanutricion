import { ArcElement, Chart, Tooltip } from 'chart.js';
import type { ReactNode } from 'react';
import { Doughnut } from 'react-chartjs-2';
import { useTranslation } from 'react-i18next';

import { formatNumber } from '../../i18n/format';
import { ChartTable } from './ChartTable';
import { cssVar } from './colors';
import { chartChrome } from './theme';

Chart.register(ArcElement, Tooltip);

interface DonutChartProps {
  labels: string[];
  values: number[];
  /** CSS custom property of each slice, in the order of the labels. */
  colorVars: string[];
  label: string;
  /** Figure in the hole of the donut. */
  centre?: ReactNode;
  formatValue?: (value: number, index: number) => string;
  testId?: string;
}

/**
 * Part-to-whole donut for a few categories: slices separated by a gap of the surface colour,
 * a legend with the value of each slice and the values as a table for screen readers.
 */
const DonutChart = ({
  labels,
  values,
  colorVars,
  label,
  centre,
  formatValue,
  testId,
}: DonutChartProps) => {
  const { i18n } = useTranslation();
  const chrome = chartChrome();
  const colors = colorVars.map((name) => cssVar(name));
  const format = formatValue ?? ((value: number) => formatNumber(value, i18n.language));

  return (
    <div className="donut" data-testid={testId}>
      <div className="donut__chart">
        <Doughnut
          role="img"
          aria-label={label}
          data={{
            labels,
            datasets: [
              {
                data: values,
                backgroundColor: colors,
                borderColor: chrome.surface,
                borderWidth: 2,
                hoverOffset: 4,
              },
            ],
          }}
          options={{
            cutout: '68%',
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: (item) => `${item.label}: ${format(Number(item.raw), item.dataIndex)}`,
                },
              },
            },
          }}
        />
        {centre && (
          <div className="donut__centre" aria-hidden="true">
            {centre}
          </div>
        )}
      </div>
      <ul className="chart-legend chart-legend--column" aria-hidden="true">
        {labels.map((name, index) => (
          <li key={name}>
            <span className="chart-legend__swatch" style={{ background: colors[index] }} />
            <span>{name}</span>
            <strong className="chart-legend__value">{format(values[index], index)}</strong>
          </li>
        ))}
      </ul>
      <ChartTable caption={label} labels={labels} values={values.map(format)} />
    </div>
  );
};

export default DonutChart;
