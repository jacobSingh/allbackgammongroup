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

        elo_chart_vars['yAxis'][1]["min"] = 0;
        elo_chart_vars['yAxis'][1]["max"] = 100;
        // elo_chart_vars['yAxis'][1]["plotBands"] = [
        //   {from: 0, to: 25, "color": '#FFAAAA',},
        //   {"from": 25, "to": 50, "color": '#FFDDDD'},
        //   {"from": 50, "to": 75, "color": '#DDDDFF'},
        //   {"from": 75, "to": 100, "color": '#AAAAFF'},
        // ];

      
        elo_chart_vars['yAxis'][1]['labels'] = {
                formatter: function () {
                    return this.value + '%';
                }
            };

        elo_chart_vars['series'][1]["tooltip"] = {"pointFormat":  '{point.y}%'};

        console.log(elo_chart_vars);
        // elo_chart_vars['series'][0]['pointStart'] = Date.UTC(2015, 0, 1),
        // elo_chart_vars['series'][0]['pointIntervalUnit']= 'year';
        aelo_chart_vars = $.extend(true, elo_chart_vars,{
        chart: {
            type: 'spline',
            zoomType: "x"
        },
        xAxis: {
            type: 'datetime',
            tickInterval: 24 * 3600*1000 * 30
        },
        // yAxis: {
        //     title: {
        //         text: 'ELO'
        //     },
        // },
        tooltip: {
            crosshairs: true,
            headerFormat: '<b>{series.name}</b><br/>',
        },
        plotOptions: {
            spline: {
                marker: {
                    radius: 4,
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
