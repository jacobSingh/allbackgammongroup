$(function () {
  $(document).ready(function() {
    if (typeof elo_stddev_chart_vars != 'undefined' && elo_stddev_chart_vars != {}) {

        $.extend(true, elo_stddev_chart_vars, {
          chart: {
            type: "areaspline",
            zoomType: "x"
          },
          xAxis: {
              plotLines: [{
              color: 'red', // Color value
              dashStyle: 'longdashdot', // Style of the plot line. Default to solid
              value: player["ELO"], // Value of where the line will appear
              width: 2, // Width of the line
              label: {
                text: player["player_name"] + " " + Math.round(player["ELO"]) + "  (" + player["percentile"] + " percentile)"
              }
            }]
          }
        });

        new Highcharts.Chart(elo_stddev_chart_vars)
      }
      if (elo_chart_vars) {
        console.log(elo_chart_vars);
        elo_chart_vars['series'][0]['tooltip'] = {'valueDecimals': 2};
        elo_chart_vars['series'][0]['pointStart'] = Date.UTC(2015, 0, 1),
        elo_chart_vars['series'][0]['pointIntervalUnit']= 'year';
        aelo_chart_vars = $.extend(true, elo_chart_vars,{
        chart: {
            type: 'spline',
            zoomType: "x"
        },
        xAxis: {
            type: 'datetime',
            tickInterval: 24 * 3600*1000 * 30
        },
        yAxis: {
            title: {
                text: 'ELO'
            },
        },
        tooltip: {
            crosshairs: true,
            shared: true
        },
        plotOptions: {
            spline: {
                marker: {
                    radius: 8,
                    lineColor: '#666666',
                    lineWidth: 1
                },
            }
        },
    });
      console.log(elo_chart_vars)
        new Highcharts.Chart(elo_chart_vars)
      }
  });
});
