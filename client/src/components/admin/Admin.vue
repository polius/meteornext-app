<template>
<div>
  <div style="background-color: #343F57; padding-top:15px; border-radius: 10px;">
    <apexchart width="100%" height="435" type="area" :options="options" :series="series" style="margin-left:-10px;"></apexchart>
  </div>
</div>
</template>

<style>
  .apexcharts-canvas.dark {
    background-color: transparent;
  }
  .apexcharts-toolbar {
    margin-right: 5px;
  }
  .apexcharts-legend-marker {
    top: -1px!important;
  }
  .apexcharts-legend-text {
    margin-right: 5px;
  }
  .apexcharts-zoom-in-icon, .apexcharts-zoom-out-icon, .apexcharts-reset-zoom-icon, .apexcharts-menu-icon {
    transform: scale(0.9);
    margin-right: 5px;
  }
  .apexcharts-zoom-icon {
    transform: scale(1.1);
    margin-right: 5px;
  }
  .apexcharts-pan-icon {
    transform: scale(0.8);
    margin-right: 5px;
  }
</style>

<script>
import VueApexCharts from 'vue-apexcharts'

export default {
  components: {
    apexchart: VueApexCharts
  },
  data: () => ({
    series: [{
      name: 'BASIC',
      data: [31, 40, 28, 51, 42, 109, 100]
    }, {
      name: 'PRO',
      data: [11, 32, 45, 32, 34, 52, 41]
    }],
    options: {
      chart: {
        id: 'test'
      },
      theme: {
        mode: 'dark',
        palette: 'palette1'
      },
      dataLabels: {
        enabled: false
      },
      stroke: {
        curve: 'smooth'
      },
      xaxis: {
        type: 'datetime',
        categories: ["2018-09-19T00:00:00", "2018-09-19T01:00:00", "2018-09-19T02:00:00", "2018-09-19T03:00:00", "2018-09-19T04:00:00", "2018-09-19T05:00:00", "2018-09-19T06:00:00"],
        labels: {
          datetimeFormatter: {
            year: 'yyyy',
            month: 'MMM \'yy',
            day: 'dd MMM',
            hour: 'HH:mm'
          },
          style: {
            fontSize: '14px',
            fontFamily: 'Roboto',
          }
        }
      },
      yaxis: {
        labels: {
          style: {
            fontSize: '14px',
            fontFamily: 'Roboto',
          }
        }
      },
      tooltip: {
        x: {
          format: 'dd/MM/yyyy'
        },
        style: {
          fontSize: '14px',
          fontFamily: 'Roboto'
        }
      },
      legend: {
        position: 'top',
        horizontalAlign: 'center',
        fontSize: '17px',
        fontFamily: 'Roboto',
      },
    }
  })
}
</script>