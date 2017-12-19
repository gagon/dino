
Highcharts.chart('container-field-balance', {
    chart: {
        backgroundColor: 'white',
        events: {
            load: function () {

                var ren = this.renderer
                //var dshift=-50;
                //var rshift=0;

                ren.label('KPC', 300+rshift, 150+dshift)
                    .attr({
                        fill: "#FFFFCC",
                        stroke: '#505050',
                        'stroke-width': 1,
                        padding: 40,
                        paddingLeft: 20,
                        r: 2,
                        width:55,
                        height:20
                    })
                    .css({
                        color: '#000000',
                        fontSize:'18px',
                        align: 'center',
                    })
                    .add()
                    .shadow(true);

                ren.label('Unit 2', 300+rshift, 450+dshift)
                  .attr({
                      fill: "#FFFFCC",
                      stroke: '#505050',
                      'stroke-width': 1,
                      padding: 40,
                      paddingLeft: 10,
                      r: 2,
                      width:60,
                      height:20
                  })
                  .css({
                      color: '#000000',
                      fontSize:'18px',
                      align: 'center',
                  })
                  .add()
                  .shadow(true);

                  ren.label('Unit 3', 700+rshift, 300+dshift)
                    .attr({
                        fill: "#FFFFCC",
                        stroke: '#505050',
                        'stroke-width': 1,
                        padding: 40,
                        paddingLeft: 10,
                        r: 2,
                        width:60,
                        height:20
                    })
                    .css({
                        color: '#000000',
                        fontSize:'18px',
                        align: 'center',
                    })
                    .add()
                    .shadow(true);




                // KPC gas mid to U3
                ren.path(['M', 0, 0, 'L', 299, 0, 'M', 298, 0,'L', 291, 5, 'M', 298, 0, 'L', 291, -5])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'orange'
                    })
                    .translate(400+rshift, 350+dshift)
                    .add();

                // KPC gas to U2
                ren.path(['M', 0, 0, 'L', 0, 198,'M', 0, 197,'L', 5, 190,'M', 0, 197,'L', -5, 190])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'orange'
                    })
                    .translate(400+rshift, 251+dshift)
                    .add();

                // U2 oil to KPC
                ren.path(['M', 0, 0, 'L', 0, 198,'M', 0,1,'L', 5, 8,'M', 0,1,'L', -5, 8])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(350+rshift, 252+dshift)
                    .add();

                // U3 oil to KPC line 1
                ren.path(['M', 0, 0, 'L', 0, 80])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(730+rshift, 220+dshift)
                    .add();

                // U3 oil to KPC line 2
                ren.path(['M', 0, 0, 'L', -273, 0,'M', -272,0,'L', -265, 5,'M', -272,0,'L', -265, -5,])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(730+rshift, 220+dshift)
                    .add();

                // U3 to ogp gas
                ren.path(['M', 0, 0, 'L', 100, 0, 'M', 99, 0,'L', 92, 5, 'M', 99, 0, 'L', 92, -5])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'orange'
                    })
                    .translate(850+rshift, 330+dshift)
                    .add();

                // U3 to ogp oil
                ren.path(['M', 0, 0, 'L', 100, 0, 'M', 99, 0,'L', 92, 5, 'M', 99, 0, 'L', 92, -5])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(850+rshift, 370+dshift)
                    .add();


                // U3 oil to MTU
                ren.path(['M', 0, 0, 'L', 0, -80,'M', 0, -79, 'L', 5, -72,'M', 0, -79, 'L', -5, -72])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(800+rshift, 300+dshift)
                    .add();

                // MTU gas to U3
                ren.path(['M', 0, 0, 'L', 0, -80,'M', 0, -1, 'L', 5, -8,'M', 0, -1, 'L', -5, -8])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'orange'
                    })
                    .translate(820+rshift, 300+dshift)
                    .add();


                // U2 oil to U3 line 1
                ren.path(['M', 0, 0, 'L', 280, 0])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(450+rshift, 480+dshift)
                    .add();

                // U2 oil to U3 line 2
                ren.path(['M', 0, 0, 'L', 0, -78,'M', 0, -77, 'L', 5, -70,'M', 0, -77, 'L', -5, -70 ])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(730+rshift, 480+dshift)
                    .add();

                // U2 gas to reinjection
                ren.path(['M', 0, 0, 'L', 0, 60,'M', 0, 59, 'L', 5, 52,'M', 0, 59, 'L', -5, 52])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'orange'
                    })
                    .translate(380+rshift, 550+dshift)
                    .add();

                // KPC oil to CPC
                ren.path(['M', 0, 0, 'L', 0, 70,'M', 0,-1,'L', 5, 7,'M', 0,-1,'L', -5, 7])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'green'
                    })
                    .translate(420+rshift, 80+dshift)
                    .add();

                // KPC fuel gas
                ren.path(['M', 0, 0, 'L', 0, 40,'M', 0,-1,'L', 5, 7,'M', 0,-1,'L', -5, 7])
                    .attr({
                        'stroke-width': 2,
                        stroke: 'orange'
                    })
                    .translate(340+rshift, 110+dshift)
                    .add();


                // OGP gas label
                ren.label('OGP gas', 955+rshift, 310+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold"
                    })
                    .add();
                // OGP gas val
                ren.label(ogpgas.toString()+' '+gasunit+'', 955+rshift, 330+dshift)
                    .attr({
                        'stroke-width': 1,
                        stroke: '#3399ff',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();

                // OGP oil label
                ren.label('OGP oil', 955+rshift, 353+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold"
                    })
                    .add();
                // OGP oil val
                ren.label(ogpoil.toString()+' '+oilunit_unstb+'', 955+rshift, 368+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();



                // MTU oil/gas label
                ren.label('MTU', 780+rshift, 165+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold"
                    })
                    .add();
                // MTU oil val
                ren.label(u3oil2mtu.toString() + ' '+oilunit_unstb+'', 780+rshift, 180+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();
                // MTU gas val
                ren.label(u3solgas2mtu.toString()+' '+gasunit+' (sol.gas)', 780+rshift, 195+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                        // padding:2,
                        // fill:'#e6ffe6'
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();

                // Gas injection label
                ren.label('Gas injection', 390+rshift, 570+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold"
                    })
                    .add();
                // Gas injection val
                ren.label(inj.toString()+' '+gasunit+'', 390+rshift, 590+dshift)
                    .attr({
                        'stroke-width': 1,
                        stroke: '#3399ff',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();

                // CPC oil label
                ren.label('CPC oil', 430+rshift, 70+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold"
                    })
                    .add();
                // CPC oil val
                ren.label(cpcoil.toString()+' '+oilunit+'', 430+rshift, 90+dshift)
                    .attr({
                        'stroke-width': 1,
                        stroke: '#3399ff',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();


                // Fuelgas label
                ren.label('Fuel gas', 330+rshift, 70+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                    })
                    .add();
                // Fuelgas val
                ren.label(fuelgas.toString()+' '+gasunit+'', 330+rshift, 85+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();



                // Total KPC gas label
                ren.label('Total KPC gas', 405+rshift, 260+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                    })
                    .add();
                // Total KPC gas val
                ren.label(kpctotgas.toString()+' '+gasunit+'', 405+rshift, 275+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();


                // KPC gas to U2 label
                ren.label('KPC gas to U2', 405+rshift, 370+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold"
                    })
                    .add();
                // KPC gas to U2 val
                ren.label(kpc2u2.toString()+' '+gasunit+'', 405+rshift, 390+dshift)
                    .attr({
                        'stroke-width': 1,
                        stroke: '#3399ff',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();


                // KPC gas to U3 label
                ren.label('KPC gas to U3', 550+rshift, 300+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold"
                    })
                    .add();
                // KPC gas to U3 val
                ren.label(kpc2u3.toString()+' '+gasunit+'', 550+rshift, 320+dshift)
                    .attr({
                        'stroke-width': 1,
                        stroke: '#3399ff',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();

                // U2 oil to U3 label
                ren.label('U2 oil to U3', 500+rshift, 485+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                    })
                    .add();
                // U2 oil to U3 val
                ren.label(u2oil2u3.toString()+' '+oilunit_unstb+'', 500+rshift, 500+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();
                // U2 sol gas to U3 val
                ren.label(u2solgas2u3.toString()+' '+gasunit+' (sol.gas)', 500+rshift, 515+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();


                // U2 oil to KPC label
                ren.label('U2 oil to KPC', 220+rshift, 380+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                        // direction:'rtl'
                    })
                    .add();
                // U2 oil to KPC val
                ren.label(u2oil2kpc.toString()+' '+oilunit_unstb+'', 220+rshift, 395+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                        // direction:'rtl'
                    })
                    .add();

                // U2 sol gas to KPC val
                ren.label(u2solgas2kpc.toString()+' '+gasunit+' (sol.gas)', 220+rshift, 410+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();


                // U3 oil to KPC label
                ren.label('U3 oil to KPC', 500+rshift, 170+dshift)
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                    })
                    .add();
                // U3 oil to KPC val
                ren.label(u3oil2kpc.toString()+' '+oilunit_unstb+'', 500+rshift, 185+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();

                // U3 sol gas to KPC val
                ren.label(u3solgas2kpc.toString()+' '+gasunit+' (sol.gas)', 500+rshift, 200+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();



                // KPC well prod arrow
                ren.path(['M', 0, 0, 'L', 123, 0, 'M', 121, 0,'L', 114, 5, 'M', 121, 0, 'L', 114, -5])
                    .attr({
                        'stroke-width': 2,
                        stroke: '#00ffff'
                    })
                    .translate(175+rshift, 175+dshift)
                    .add();


                // KPC well prod
                ren.label('Wells production', 175+rshift, 180+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                    })
                    .add();
                // Qoil val
                ren.label('Qoil: '+kpcqoil+' '+oilunit_unstb+'', 175+rshift, 195+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();
                // Qgas val
                ren.label('Qgas: '+kpcqgas+' '+gasunit+'', 175+rshift, 210+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();
                // GOR val
                ren.label('GOR: '+kpcgor+' m3/m3', 175+rshift, 225+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        // color:'#b36b00',
                    })
                    .add();


                // U2 well prod arrow
                ren.path(['M', 0, 0, 'L', 123, 0, 'M', 121, 0,'L', 114, 5, 'M', 121, 0, 'L', 114, -5])
                    .attr({
                        'stroke-width': 2,
                        stroke: '#00ffff'
                    })
                    .translate(175+rshift, 475+dshift)
                    .add();


                // U2 well prod
                ren.label('Wells production', 175+rshift, 480+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                    })
                    .add();
                // Qoil val
                ren.label('Qoil: '+u2qoil+' '+oilunit_unstb+'', 175+rshift, 495+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();
                // Qgas val
                ren.label('Qgas: '+u2qgas+' '+gasunit+'', 175+rshift, 510+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();
                // GOR val
                ren.label('GOR: '+u2gor+' m3/m3', 175+rshift, 525+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        // color:'#b36b00',
                    })
                    .add();




                // U3 well prod arrow
                ren.path(['M', 0, 0, 'L', 0, -80,'M', 0, -79, 'L', 5, -72,'M', 0, -79, 'L', -5, -72])
                    .attr({
                        'stroke-width': 2,
                        stroke: '#00ffff'
                    })
                    .translate(780+rshift, 482+dshift)
                    .add();

                // U3 well prod
                ren.label('Wells production', 790+rshift, 420+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '12px',
                        fontWeight:"bold",
                    })
                    .add();
                // Qoil val
                ren.label('Qoil: '+u3qoil+' '+oilunit_unstb+'', 790+rshift, 435+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#008000',
                    })
                    .add();
                // Qgas val
                ren.label('Qgas: '+u3qgas+' '+gasunit+'', 790+rshift, 450+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        color:'#b36b00',
                    })
                    .add();
                // GOR val
                ren.label('GOR: '+u3gor+' m3/m3', 790+rshift, 465+dshift)
                    .attr({
                        // 'stroke-width': 1,
                        // stroke: '#00ff00',
                    })
                    .css({
                        fontSize: '10px',
                        // color:'#b36b00',
                    })
                    .add();
            }
        }
    },
    title: {
        text: '',
    },
    exporting: {
        enabled: false,

      // buttons: [
      //   { // day button
      //     text: 'Day',
      //     x: -75,
      //     onclick: function () {
      //       var data2session={};
      //       data2session["rate"]="day";
      //
      //       $.ajax({
      //           type: "POST",
      //           url: "/rate_2session",
      //           // The key needs to match your method's input parameter (case-sensitive).
      //           data: JSON.stringify(data2session),
      //           contentType: "application/json; charset=utf-8",
      //           dataType: "json",
      //           success: function(data){
      //             location.href="/field_balance";
      //           },
      //           failure: function(errMsg) {
      //               alert(errMsg);
      //           }
      //       });
      //     },
      //   },
      //   { // hour button
      //     text: 'Hour',
      //     // x: -100,
      //     onclick: function () {
      //       var data2session={};
      //       data2session["rate"]="hour";
      //
      //       $.ajax({
      //           type: "POST",
      //           url: "/rate_2session",
      //           // The key needs to match your method's input parameter (case-sensitive).
      //           data: JSON.stringify(data2session),
      //           contentType: "application/json; charset=utf-8",
      //           dataType: "json",
      //           success: function(data){
      //             alert("hour");
      //             window.location.href="/field_balance";
      //           },
      //           failure: function(errMsg) {
      //               alert(errMsg);
      //           }
      //       });
      //     },
      //   },
      //   // { // calculate button
      //   //   text: 'Calculate',
      //   //   theme: {
      //   //     fill: '#F0F0F0 ',
      //   //     stroke: '#888',
      //   //   },
      //   //   x: -200,
      //   //   onclick: function () {
      //   //     location.href="/field_balance/calculate";
      //   //   },
      //   // },
      // ]
    },

});


$(document).on("click", "#calculate_fb", function() {


  var cpcoil_val=$('#cpcoil_val').val();
  var cpcoil_unit=$('#cpcoil_unit').val();
  var ogpgas_val=$('#ogpgas_val').val();
  var ogpgas_unit=$('#ogpgas_unit').val();
  var ogpoil_val=$('#ogpoil_val').val();
  var ogpoil_unit=$('#ogpoil_unit').val();
  var inj_val=$('#inj_val').val();
  var inj_unit=$('#inj_unit').val();
  var fuelgas_val=$('#fuelgas_val').val();
  var fuelgas_unit=$('#fuelgas_unit').val();
  var u3oil2mtu_val=$('#u3oil2mtu_val').val();
  var u3oil2mtu_unit=$('#u3oil2mtu_unit').val();
  var u2oil2u3_val=$('#u2oil2u3_val').val();
  var u2oil2u3_unit=$('#u2oil2u3_unit').val();
  var kpc2u2_val=$('#kpc2u2_val').val();
  var kpc2u2_unit=$('#kpc2u2_unit').val();

  var data2session={};
  data2session["cpcoil_val"]=cpcoil_val;
  data2session["ogpgas_val"]=ogpgas_val;
  data2session["ogpoil_val"]=ogpoil_val;
  data2session["inj_val"]=inj_val;
  data2session["fuelgas_val"]=fuelgas_val;
  data2session["u3oil2mtu_val"]=u3oil2mtu_val;
  data2session["u2oil2u3_val"]=u2oil2u3_val;
  data2session["kpc2u2_val"]=kpc2u2_val;

  data2session["cpcoil_unit"]=cpcoil_unit;
  data2session["ogpgas_unit"]=ogpgas_unit;
  data2session["ogpoil_unit"]=ogpoil_unit;
  data2session["inj_unit"]=inj_unit;
  data2session["fuelgas_unit"]=fuelgas_unit;
  data2session["u3oil2mtu_unit"]=u3oil2mtu_unit;
  data2session["u2oil2u3_unit"]=u2oil2u3_unit;
  data2session["kpc2u2_unit"]=kpc2u2_unit;


  $.ajax({
      type: "POST",
      url: "/fb_calc_2session",
      // The key needs to match your method's input parameter (case-sensitive).
      data: JSON.stringify(data2session),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(data){

      },
      failure: function(errMsg) {
          alert(errMsg);
      }
  });
  window.location.reload();


});
