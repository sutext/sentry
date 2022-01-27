import {InjectedRouter} from 'react-router';
import {Query} from 'history';

import AreaChart from 'sentry/components/charts/areaChart';
import ChartZoom from 'sentry/components/charts/chartZoom';
import ErrorPanel from 'sentry/components/charts/errorPanel';
import LineChart from 'sentry/components/charts/lineChart';
import ReleaseSeries from 'sentry/components/charts/releaseSeries';
import TransitionChart from 'sentry/components/charts/transitionChart';
import TransparentLoadingMask from 'sentry/components/charts/transparentLoadingMask';
import Placeholder from 'sentry/components/placeholder';
import {IconWarning} from 'sentry/icons';
import {Series} from 'sentry/types/echarts';
import {axisLabelFormatter, tooltipFormatter} from 'sentry/utils/discover/charts';
import getDynamicText from 'sentry/utils/getDynamicText';
import {Theme} from 'sentry/utils/theme';

type Props = {
  loading: boolean;
  reloading: boolean;
  theme: Theme;
  errored: boolean;
  queryExtra: Query;
  router: InjectedRouter;
  series?: Series[];
  timeFrame?: {
    start: number;
    end: number;
  };
} & Omit<React.ComponentProps<typeof ReleaseSeries>, 'children' | 'queryExtra'> &
  Pick<React.ComponentProps<typeof LineChart>, 'onLegendSelectChanged' | 'legend'>;

function Content({
  errored,
  theme,
  series: data,
  timeFrame,
  start,
  end,
  period,
  projects,
  environments,
  loading,
  reloading,
  legend,
  utc,
  queryExtra,
  router,
  onLegendSelectChanged,
}: Props) {
  if (errored) {
    return (
      <ErrorPanel>
        <IconWarning color="gray500" size="lg" />
      </ErrorPanel>
    );
  }

  const chartOptions = {
    grid: {
      left: '10px',
      right: '10px',
      top: '40px',
      bottom: '0px',
    },
    seriesOptions: {
      showSymbol: false,
    },
    tooltip: {
      trigger: 'axis' as const,
      valueFormatter: tooltipFormatter,
    },
    xAxis: timeFrame
      ? {
          min: timeFrame.start,
          max: timeFrame.end,
        }
      : undefined,
    yAxis: {
      axisLabel: {
        color: theme.chartLabel,
        // p50() coerces the axis to be time based
        formatter: (value: number) => axisLabelFormatter(value, 'p50()'),
      },
    },
  };

  const colors = (data && theme.charts.getColorPalette(data.length - 2)) || [];

  // Create a list of series based on the order of the fields,
  // We need to flip it at the end to ensure the series stack right.
  const series = data
    ? data
        .map((values, i: number) => {
          return {
            ...values,
            color: colors[i],
            lineStyle: {
              opacity: 0,
            },
          };
        })
        .reverse()
    : [];

  return (
    <ChartZoom router={router} period={period} start={start} end={end} utc={utc}>
      {zoomRenderProps => (
        <ReleaseSeries
          start={start}
          end={end}
          queryExtra={queryExtra}
          period={period}
          utc={utc}
          projects={projects}
          environments={environments}
        >
          {({releaseSeries}) => (
            <TransitionChart loading={loading} reloading={reloading}>
              <TransparentLoadingMask visible={reloading} />
              {getDynamicText({
                value: (
                  <AreaChart
                    {...zoomRenderProps}
                    {...chartOptions}
                    legend={legend}
                    onLegendSelectChanged={onLegendSelectChanged}
                    series={[...series, ...releaseSeries]}
                  />
                ),
                fixed: <Placeholder height="200px" testId="skeleton-ui" />,
              })}
            </TransitionChart>
          )}
        </ReleaseSeries>
      )}
    </ChartZoom>
  );
}

export default Content;