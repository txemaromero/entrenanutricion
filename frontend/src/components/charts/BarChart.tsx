import { BarElement, CategoryScale, Chart, LinearScale, Tooltip, type Plugin } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { useTranslation } from 'react-i18next';

import { formatNumber } from '../../i18n/format';
import { ChartTable } from './ChartTable';
import { cssVar } from './colors';
import { axisNumber, chartChrome } from './theme';

Chart.register(BarElement, CategoryScale, LinearScale, Tooltip);

interface Reference {
  value: number;
  /** Legend text of the line, e.g. "Objetivo · 1700 kcal". */
  label: string;
}

interface BarChartProps {
  labels: string[];
  values: number[];
  label: string;
  /** CSS custom property with the bar colour. */
  colorVar: string;
  horizontal?: boolean;
  testId?: string;
  /** How a value reads in the tooltip and in the table (the number by default). */
  formatValue?: (value: number, index: number) => string;
  height?: number;
  /** A dashed reference line (vertical charts), e.g. a daily target; it adds a legend. */
  reference?: Reference;
  /** Legend text of the bars when there is a reference line (the chart label by default). */
  seriesLabel?: string;
  /** Test id of each row of the accessible table. */
  rowTestId?: string;
}

/** Dashed horizontal line across the plot at `value`, in the secondary ink. */
/** Category names longer than this are shortened on the axis of horizontal charts. */
const AXIS_LABEL_MAX = 22;

const shorten = (label: string) =>
  label.length > AXIS_LABEL_MAX ? `${label.slice(0, AXIS_LABEL_MAX - 1).trimEnd()}…` : label;

const referenceLine = (value: number, color: string): Plugin<'bar'> => ({
  id: 'referenceLine',
  afterDatasetsDraw: (chart) => {
    const { ctx, chartArea, scales } = chart;
    const y = scales.y.getPixelForValue(value);
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(chartArea.left, y);
    ctx.lineTo(chartArea.right, y);
    ctx.stroke();
    ctx.restore();
  },
});

/**
 * Single-series bar chart: thin bars rounded at the data end, square at the baseline, a
 * hairline grid on the value axis only, and the values as a table for screen readers.
 */
const BarChart = ({
  labels,
  values,
  label,
  colorVar,
  horizontal = false,
  testId,
  formatValue,
  height,
  reference,
  seriesLabel,
  rowTestId,
}: BarChartProps) => {
  const { i18n } = useTranslation();
  const chrome = chartChrome();
  const color = cssVar(colorVar);
  const format = formatValue ?? ((value: number) => formatNumber(value, i18n.language));
  const valueAxis = horizontal ? 'x' : 'y';
  const categoryAxis = horizontal ? 'y' : 'x';
  const withReference = reference && !horizontal ? reference : undefined;

  return (
    <div data-testid={testId}>
      <div style={{ height: height ?? (horizontal ? Math.max(160, labels.length * 34) : 260) }}>
        <Bar
          role="img"
          aria-label={label}
          plugins={withReference ? [referenceLine(withReference.value, chrome.text)] : []}
          data={{
            labels,
            datasets: [
              {
                label: seriesLabel ?? label,
                data: values,
                backgroundColor: color,
                borderRadius: 4,
                borderSkipped: 'start',
                maxBarThickness: 24,
              },
            ],
          }}
          options={{
            indexAxis: horizontal ? 'y' : 'x',
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  title: (items) => labels[items[0]?.dataIndex ?? 0] ?? '',
                  label: (item) => format(Number(item.raw), item.dataIndex),
                },
              },
            },
            scales: {
              [valueAxis]: {
                beginAtZero: true,
                suggestedMax: withReference ? withReference.value * 1.1 : undefined,
                grid: { color: chrome.grid },
                border: { display: false },
                ticks: {
                  precision: 0,
                  color: chrome.text,
                  callback: (value) => axisNumber(Number(value), i18n.language),
                },
              },
              [categoryAxis]: {
                grid: { display: false },
                border: { color: chrome.grid },
                // A few categories always show every label; long series skip some.
                ticks: {
                  color: chrome.text,
                  maxRotation: 0,
                  autoSkip: labels.length > 8,
                  autoSkipPadding: 12,
                  ...(horizontal && {
                    callback: (_: unknown, index: number) => shorten(labels[index] ?? ''),
                  }),
                },
              },
            },
          }}
        />
      </div>
      {withReference && (
        <ul className="chart-legend" aria-hidden="true">
          <li>
            <span className="chart-legend__swatch" style={{ background: color }} />
            {seriesLabel ?? label}
          </li>
          <li>
            <span className="chart-legend__line" />
            {withReference.label}
          </li>
        </ul>
      )}
      <ChartTable
        caption={withReference ? `${label} (${withReference.label})` : label}
        labels={labels}
        values={values.map(format)}
        rowTestId={rowTestId}
      />
    </div>
  );
};

export default BarChart;
