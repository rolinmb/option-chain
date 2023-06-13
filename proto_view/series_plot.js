var clicks = 0;

function updateSeriesPlot(div, data, layout){
    if(!div.hasChildNodes() || clicks < 2){
        Plotly.plot(div, data, layout);
        clicks++;
    }else{
        Plotly.newPlot(div, data, layout)
        clicks = 1;
    }
}

function readSeriesCSV(){
    dates = [];
    adjc_prices = [];
    var files = document.querySelector('.series_csv').files;
    if(files.length > 0){
        var file = files[0];
        var reader = new FileReader();
        reader.readAsText(file);
        reader.onload = function(event){
            var csv_data = event.target.result;
            var row_data = csv_data.split('\n');
            for(var row = 1; row < row_data.length; row++){
                col_data = row_data[row].split(',');
                dates.push(col_data[1]) // date string
                adjc_prices.push(col_data[6]) // adjusted close price
            }
        };
    }else{
        alert("Please select a .csv file")
    }
    var data = [
        { 
            x: dates, 
            y: adjc_prices, 
            type: 'scatter'
        }
    ];
    var layout = {
        yaxis : {
            type: 'log',
            autorange: true
        }
    };
    updateSeriesPlot(document.getElementById('series_plot'), data, layout);
}