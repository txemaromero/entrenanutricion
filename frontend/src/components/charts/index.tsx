import { IonSkeletonText } from '@ionic/react';
import { lazy, Suspense, type ComponentProps } from 'react';

/** Charts are code-split so Chart.js only loads on the screens that draw one. */
const LazyWeightChart = lazy(() => import('./WeightChart'));
const LazyMacroDonut = lazy(() => import('./MacroDonut'));
const LazyBarChart = lazy(() => import('./BarChart'));
const LazyLoadChart = lazy(() => import('./LoadChart'));
const LazyLineChart = lazy(() => import('./LineChart'));
const LazyDonutChart = lazy(() => import('./DonutChart'));

const Placeholder = ({ height }: { height: number }) => (
  <IonSkeletonText animated style={{ height, width: '100%', borderRadius: 12 }} />
);

export const WeightChart = (props: ComponentProps<typeof LazyWeightChart>) => (
  <Suspense fallback={<Placeholder height={props.compact ? 180 : 280} />}>
    <LazyWeightChart {...props} />
  </Suspense>
);

export const MacroDonut = (props: ComponentProps<typeof LazyMacroDonut>) => (
  <Suspense fallback={<Placeholder height={280} />}>
    <LazyMacroDonut {...props} />
  </Suspense>
);

export const BarChart = (props: ComponentProps<typeof LazyBarChart>) => (
  <Suspense fallback={<Placeholder height={props.height ?? 260} />}>
    <LazyBarChart {...props} />
  </Suspense>
);

export const LoadChart = (props: ComponentProps<typeof LazyLoadChart>) => (
  <Suspense fallback={<Placeholder height={200} />}>
    <LazyLoadChart {...props} />
  </Suspense>
);

export const LineChart = (props: ComponentProps<typeof LazyLineChart>) => (
  <Suspense fallback={<Placeholder height={props.height ?? 220} />}>
    <LazyLineChart {...props} />
  </Suspense>
);

export const DonutChart = (props: ComponentProps<typeof LazyDonutChart>) => (
  <Suspense fallback={<Placeholder height={200} />}>
    <LazyDonutChart {...props} />
  </Suspense>
);
