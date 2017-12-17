
$(function () {

    // prep series data, convert date string to UTC for chart, add formatting, also save series original data
    // var series_orig=series;
    trend_id_cnt=0;

    for (i=0;i<series.length;i++){

      for(j=0;j<series[i]["data"].length;j++){
        var result=parse_trend_series(series,i)
        var dt_str=result[0]
        var val=result[1]
        var dt = Date.UTC(
          parseInt(dt_str[0]),parseInt(dt_str[1])-1,parseInt(dt_str[2])
        );
        series[i]["data"][j]=[dt,val]
      };



      if(series[i]["name"]=="WT "+trend_type || series[i]["name"]=="PROSPER "+trend_type){

        if(series[i]["name"]=="WT "+trend_type){
          series[i]["marker"]={
            fillColor: '#7cb5ec',
            lineColor: 'black',
            lineWidth: 1,
            symbol: "diamond",
            radius:4

          };

        }else{

          series[i]["marker"]={
            fillColor: "yellow",
            lineColor: 'black',
            lineWidth: 1,
            symbol: "triangle",
            radius:4


          };

        };

      }else if(series[i]["name"]=="Cum Oil"){

        series[i]["color"]="green";
        series[i]["marker"]= {
          enabled: false
        };
        series[i]["lineWidth"]=1;
        series[i]["yAxis"]=1;

      }else if(series[i]["name"]=="Cum Gas"){

        series[i]["color"]="orange";
        series[i]["marker"]= {
          enabled: false
        };
        series[i]["lineWidth"]=1;
        series[i]["yAxis"]=1;

      }else{



        series[i]["marker"]={
          enabled: false
        };

        if(trend_id_cnt>0){
          series[i]["dashStyle"]="longdash"
          series[i]["lineWidth"]=1;
        }else{
          series[i]["name"]=series[i]["name"]+" (Current)"
          series[i]["lineWidth"]=2;
        };

        trend_id_cnt++;

    };
        };

    Highcharts.chart('container-main-chart', {
        chart: {
          type: 'scatter',
          zoomType: 'xy'
        },
        title: {
          text: 'Well '+wellname+' - '+trend_type+' trend'
        },
        xAxis: {
          type: 'datetime',
          minRange:1
        },
        yAxis: [{
          title: {
            text: trend_type+" ["+trend_unit+"]"
          },
          min: 0
        },{
          title: {
            text: "Cumulative production [m3 or km3]"
          },
          min: 0,
          opposite:true
        }],
        tooltip: {
          headerFormat: '<b>{series.name}</b><br>',
          pointFormat: '{point.x:%Y-%m-%d}<br> {point.y:.0f} Sm3/Sm3'
        },

        legend: {
          align: 'right',
          verticalAlign: 'middle',
          layout:"vertical"
          // verticalAlign: 'middle',
          // y : 25
        },
        series:series


    });

    data=get_new_trend_data();
    calc_val_slope(data);

});


$(document).on("click", "#update_all", function() {
  new_trend2plot();
});

function new_trend2plot() {

  data=get_new_trend_data();

  new_trend_val=calc_val_slope(data);

  var chart = $('#container-main-chart').highcharts();

  for(i=0;i<chart.series.length;i++){
    if (chart.series[i].name=="New trend"){
      chart.series[i].remove();
    };
  };

  for(i=0;i<chart.series.length;i++){
    if (chart.series[i].name=="New trend val"){
      chart.series[i].remove();
    };
  };

  chart.addSeries({
    name: "New trend",
    data: data,
    lineWidth: 2,
    color:"red",
    marker: {
      enabled: false
    }
  });

  chart.addSeries({
    name: "New trend val",
    data: [new_trend_val],
    color:"red",
    marker: {
      symbol: 'triangle',
      radius: 7
    }
  });


};


function get_new_trend_data(){

  data_arr=[];
  i=1
  $('#new_tr_table tbody').children('tr').each(function () {
    var val = parseFloat($(this).find(".v").text());
    var dt_str = $(this).find(".d").text().split("-");
    var dt = Date.UTC(
      parseInt(dt_str[0]),parseInt(dt_str[1])-1,parseInt(dt_str[2])
    );
    data_arr.push([dt,val]);
    i+=1;
  });

  return data_arr;

};



function calc_val_slope(array){

  // transpose data array for interpolation
  var newArray = array[0].map(function(col, i) {
    return array.map(function(row) {
      return row[i]
    })
  });

  var dates=newArray[0];
  var vals=newArray[1];

  var dt_str=$('#calc_date').text().split("-")
  var dt = Date.UTC(
    parseInt(dt_str[0]),parseInt(dt_str[1])-1,parseInt(dt_str[2])
  );

  var val=Linterp(dates,vals,dt);
  $('#calc_val').text(val.toFixed(1));

  if(dates.length>1){

    var slope=(vals[vals.length-2]-vals[vals.length-1])/(dates[dates.length-2]-dates[dates.length-1])*8.64e+7 // milliseconds to day conversion
    $('#calc_slope').text(slope.toFixed(6));

  } else {
    $('#calc_slope').text("check input data..");
  };

  return [dt,val];

};



function Linterp(rx,ry,x){ // function for linear interpolation/extrapolation
  var nR=rx.length;
  if(nR<2){
    return;
  };
  if(x<rx[0]){
    var l1=0;
    var l2=1;
  } else if (x>rx[nR-1]) {
    l1=nR-1;
    l2=nR-2;
  } else {
    for(lR=0;lR<nR;lR++){
      if(rx[lR]==x){
        y=ry[lR];
        return y;
      } else if (rx[lR]>x) {
        l1=lR;
        l2=lR-1;
        break;
      };
    };
  };
  y=ry[l1]+(ry[l2]-ry[l1])*(x-rx[l1])/(rx[l2]-rx[l1]);
  return y;

};


function parse_trend_series(series,i){
  if(series[i]["name"].indexOf("WT ") !=-1 || series[i]["name"].indexOf("PROSPER ") !=-1 || series[i]["name"].indexOf("Cum Oil") !=-1 || series[i]["name"].indexOf("Cum Gas") !=-1){
    var dt_str=series[i]["data"][j][0].split("-")
    var val=series[i]["data"][j][1]
  }else{
    var dt_str=series[i]["data"][j]["date"].split("-")
    var val=series[i]["data"][j]["value"]
  }

  return [dt_str,val]
};
