$( document ).ready(function() {

    $(document).foundation();
    // Refresh
    var refresh_on = setInterval(refresh_visibility, 5000);

    // Controls
    $( "#visibilitySwitch" ).click(function() {
        if (this.checked) {
            refresh_on = setInterval(refresh_visibility, 5000);
        } else {
            clearInterval(refresh_on);
        }
    });

    $( "#clear_visibility" ).click(function() {
        $.get( "visibility/clear", function( data ) {
            alert(data);
        });
    });
    
    // Visibility selection
    $( "#visibility_selected" ).selectable();
    $( "#vservices" ).selectable();

    $( "#visibility_selected" ).on( "selectableselected", function() {
        var vselected = [];
        $(".ui-selected", this).each(function() {
            vselected.push(this.innerHTML);
        });
        set_visibility(vselected);
    });

    $( "#visibility_selected" ).on( "selectableunselected", function() {
        var vselected = [];
        $(".ui-selected", this).each(function() {
            vselected.push(this.innerHTML);
        });
        set_visibility(vselected);
    });
    
    var vse = [] ;
    $("ol#vservices > li.ui-widget-content.ui-selectee", this).each(function() {
        vse.push(this.innerHTML)
    });
    for (var i=0; i<vse.length; i++) {
        $("#visibility_selected > li", this).each(function() {
            if (vse[i] === this.innerHTML.replace(/-/g, '_')) {
                $(this).addClass("ui-selected");
            }
        });
    }

    $( "#visibility_accordion" ).accordion({collapsible: true, active: false});


});

function set_visibility(vselected) {
    
    var services = {};
    var y = [];
    vselected.forEach(function(element) {
        var x = {};
        x['name'] = element
        y.push(x)
    });
    services['services'] = y 
    
    $.ajax({
        type: "POST",
        url: "visibility/set",
        data: JSON.stringify(services),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        async: false,
        success: function(data){alert(data);},
        failure: function(errMsg) {
            alert(errMsg);
        }
    });

}

function refresh_visibility() {
    $.get( "visibility/get/stats/all", function( data ) {

        // Response Times
        var head1 = '<div class="cell">Service</div>';
        var head2 = '<div class="cell">Min(ms)</div>';
        var head3 = '<div class="cell">Avg(ms)</div>';
        var head4 = '<div class="cell">Max(ms)</div>';
        var content = head1 + head2 + head3 + head4;
        for (var i=0; i<data.response_times.length; i++) {
            var o = data.response_times[i];
            content = content + 
                      '<div class="cell bbb">' +
                      o.name + '</div><div class="cell bbb">' +
                      o.min + '</div><div class="cell bbb">' +
                      o.avg + '</div><div class="cell bbb">' +
                      o.max + '</div>';
        }
        $( ".tracing_rt" ).html( content );

        // System Counts
        content = '<div class="vtoplevel"><a>Traces: ' + 
                  data.trace_count + "</a><br><a>Spans: " + 
                  data.span_count + "</a><br><a>Metrics: " +
                  data.metric_count + "</a></div>" ;
        $( ".system_counts" ).html( content );

        // Distinct
        update_distinct('request_urls', data)
        update_distinct('user_agents', data)
        update_distinct('status_codes', data)
        update_distinct('op_names', data)
        update_distinct('node_ids', data)
        update_distinct('upstream_clusters', data)

        // Tracing Charts, URL count
        $(".span_urls_all").empty();
        var el = document.createElement("div");
        $(".span_urls_all").append(el);
        
        var data1 = [];
        for (var i=0; i<data.request_url_count.length; i++) {
           data1.push({
             "URLs": data.request_url_count[i][0],
             "Count": data.request_url_count[i][1]
           });
         }

         var vis1 = new candela.components.BarChart(el, {
           data: data1,
           x: "URLs",
           y: "Count",
           width: 600,
           height: 400,
           renderer: "svg"
         });
         vis1.render();

        // URL/status code count
        $(".status_codes_all").empty();
        var el1 = document.createElement("div");
        $(".status_codes_all").append(el1);
       
        data1 = [];
        for (var i=0; i<data.status_code_count.length; i++) {
           data1.push({
             "Status Codes, URLs": data.status_code_count[i][0],
             "Count": data.status_code_count[i][1]
           });
         }

         var vis2 = new candela.components.BarChart(el1, {
           data: data1,
           x: "Status Codes, URLs",
           y: "Count",
           width: 600,
           height: 400,
           renderer: "svg"
         });
         vis2.render();

        // URL/service count
        $(".span_node_urls_all").empty();
        var el2 = document.createElement("div");
        $(".span_node_urls_all").append(el2);

        data1 = [];
        for (var i=0; i<data.node_url_count.length; i++) {
           data1.push({
             "Services, URLs": data.node_url_count[i][0],
             "Count": data.node_url_count[i][1]
           });
         }

         var vis3 = new candela.components.BarChart(el2, {
           data: data1,
           x: "Services, URLs",
           y: "Count",
           width: 600,
           height: 800,
           renderer: "svg"
         });
         vis3.render();

        // Plotly, user-agent %
        data1 = [];
        var ua_values = [];
        var ua_labels = [];
        var ua_sum = 0;
        for (var i=0; i<data.user_agent_count.length; i++) {
               ua_sum = ua_sum + data.user_agent_count[i][1];
        }
        var yval = 0;
        for (var i=0; i<data.user_agent_count.length; i++) {
           yval = Math.round(( data.user_agent_count[i][1] / ua_sum )  * 100);
           ua_values.push(yval);
           ua_labels.push(data.user_agent_count[i][0]);
         }
        data1 = [{
            values: ua_values,
            labels: ua_labels,
            type:  'pie'
        }]
        Plotly.newPlot('span_user_agents_all', data1); 

        // Node_id count
        $(".span_node_id_all").empty();
        var el3 = document.createElement("div");
        $(".span_node_id_all").append(el3);

        data1 = [];
        for (var i=0; i<data.node_id_count.length; i++) {
           data1.push({
             "Services": data.node_id_count[i][0],
             "Count": data.node_id_count[i][1]
           });
         }

         var vis4 = new candela.components.BarChart(el3, {
           data: data1,
           x: "Services",
           y: "Count",
           width: 600,
           height: 400,
           renderer: "svg"
         });
         vis4.render();

        // Plotly, metrics
        $("#metrics_graphs").empty();
        var toggle = true;
        for (var i=0; i<data.metrics_time.length; i++) {
            var metric = data.metrics_time[i];
            var po = '';
            if (toggle) { 
                po = ' small-offset-2';
                toggle = false;
            } else {
                toggle = true;
            }
            var portlet = '<div class="large-4 cell clover-portlet' +
                          po + '">';
            var mdiv = '<div id="' + metric.name  + '"></div>';
            var m_html = portlet + mdiv + '</div>';
            $("#metrics_graphs").append(m_html);

            data1 = [];
            var x_values = [];
            var y_values = [];
            for (var j=0; j<metric.values.length; j++) {
               x_values.push(j);
               y_values.push(metric.values[j]);
             }
            data1 = [{
                x: x_values,
                y: y_values,
                type:  'scatter'
            }]
            var m_title = metric.service + '<br>' + metric.prefix + '<br>' +
                          metric.suffix;
            var layout = {
                title: m_title
            };
            Plotly.newPlot(metric.name, data1, layout);
        }

    });
    $.get( "visibility/metrics", function( data ) {
        $( ".service_metrics" ).html( data );
    });

}

function update_distinct(dkey, data) {
    content = '';
    for (var i=0; i<data[dkey].length; i++) {
        content = content + data[dkey][i] + '<br>';
    }
    var container = '.' + dkey;
    $(container).html(content);
}
