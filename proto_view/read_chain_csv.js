var func_names = [
    'TheoDif','IV','MidIV',
    'Delta','Elasticity','Vega','Rho','Epsilon','Theta',
    'Gamma','Vanna','Charm','Vomma','Veta','Speed',
    'Zomma','Color','Ultima'
];

var func_strs = [
    'TheoDif','&sigma;','Mid&sigma;',
    '&Delta;','&lambda;','Vega','&rho;','&epsilon;','&Theta;',
    '&Gamma;','Vanna','Charm','Vomma','Veta','Speed',
    'Zomma','Color','Ultima'
];

/*
function buildSurfaceImages(ticker, div){
    for(var i = 0; i < 18; i++){
        var img_header = document.createElement('h3');
        img_header.innerHTML = '$'+ticker+' Option Chain '+func_strs[i]+' & '+func_strs[i]+' Gradient Surfaces';
        div.appendChild(img_header);
        var img_elem = document.createElement('img');
        img_elem.src = '../png_outputs/chains/'+ticker+'_'+func_names[i]+'_quadsurface.png';
        div.appendChild(img_elem);
    }
}

function updateIndividualPlots(fresh, call_data, put_data, c_layout, p_layout){
    var call_div = document.getElementById('call_surfaces');
    var put_div = document.getElementById('put_surfaces');
    if(fresh){ // Create new children plots of call/put surfaces containers
        for(let i = 0; i < 18; i++){
            var new_call_elmnt = document.createElement('div');
            call_div.appendChild(new_call_elmnt);
            Plotly.plot(call_div, call_data, c_layout);
            var new_put_elmnt = document.createElement('div');
            put_div.appendChild(new_put_elmnt);
            Plotly.plot(put_div, put_data, p_layout);
        }
    }else{ // Get children plot divs of main call/put surfaces containers and update
       var c_children = call_div.children;
       var p_children = put_div.children;
        for(let i = 0; i < c_children.length; i++){
            Plotly.newPlot(c_children[i], call_data, c_layout);
            Plotly.newPlot(p_children[i], put_data, p_layout);
        }
    }
}
*/

var clicks = 0;

function clearChildNodes(div){
    while(div.firstChild){
        div.removeChild(div.firstChild);
    }
}

function updateSurfacesDiv(ticker, ytes, strikes, call_vals, put_vals){
    // var div = document.getElementById('surfaces_area');
    console.log('Length of ytes:',ytes.length);
    console.log('Length of ytes:',strikes.length);
    console.log('Length of call_vals: '+String(call_vals.length)+'; Length of put_vals: '+String(put_vals.length))
    var call_div = document.getElementById('call_surfaces');
    var put_div = document.getElementById('put_surfaces');
    var c_data = [{
        type: 'surface',
        x: strikes,
        y: ytes,
        z:call_vals
    }];
    var p_data = [{
        type: 'surface',
        x: strikes,
        y: ytes,
        z: put_vals
    }];
    var c_layout = { title: ticker+' Call IV', autosize: false, width: 750, height: 750 };
    var p_layout = { title: ticker+' Put IV', autosize: false, width: 750, height: 750 };
    if(!call_div.hasChildNodes() || clicks < 2){
        // buildSurfaceImages(ticker, div);
        // updateIndividualPlots(true, c_data, p_data, c_layout, p_layout); // Create new plot divs for all calculations
        Plotly.plot(call_div, c_data, c_layout);
        Plotly.plot(put_div, p_data, p_layout);
        clicks++;
    }else{
        // clearChildNodes(div);
        // buildSurfaceImages(ticker, div);
        // updateIndividualPlots(true, c_data, p_data, c_layout, p_layout); // Create new plot divs for all calculations
        Plotly.newPlot(call_div, c_data, c_layout);
        Plotly.newPlot(put_div, p_data, p_layout);
        clicks = 1;
    }
}

function readChainCSV(){
    var unique_ytes = [];
    var strikes_yte = []; // list of lists
    var call_vals = []; // list of lists
    var put_vals = []; // list of lists
    var exp_num = 0;
    var files = document.querySelector('.chain_csv').files;
    if(files.length > 0){
        var file = files[0];
        var reader = new FileReader();
        reader.readAsText(file);
        reader.onload = function(event){
            var ticker = file.name.substring(0, file.name.indexOf('_'));
            var csv_data = event.target.result;
            var row_data = csv_data.split('\n'); // Every row in the .csv has Call and Put data
            var tbody_elmnt = document.getElementById('chain_table').getElementsByTagName('tbody')[0];
            tbody_elmnt.innerHTML = "";
            for(var row = 1; row < row_data.length; row++){
                var new_row = tbody_elmnt.insertRow();
                var col_data = row_data[row].split(',');
                if(col_data.length === 1 && col_data[0].trim() === ''){
                    continue;
                }
                // Detect new YTE/Expiration
                if(!unique_ytes.includes(col_data[3])){
                    unique_ytes.push(col_data[3]);
                    exp_num++;
                    strikes_yte.push([]); // new lists for each expiration
                    call_vals.push([]);
                    put_vals.push([]);
                }
                strikes_yte[exp_num-1].push(col_data[6]); // Unique strkes for YTE
                call_vals[exp_num-1].push(col_data[16]); // Call IV for strike and YTE
                put_vals[exp_num-1].push(col_data[42]); // Put IV for strike and YTE
                for(var col = 0; col < col_data.length; col++){ // Building HTML table
                    var new_cell = new_row.insertCell();
                    if(col === 4){
                        new_cell.innerHTML = col_data[col]+' '+col_data[col+1];
                        col++;
                    }else{
                        new_cell.innerHTML = col_data[col];
                    }
                }
            }
            updateSurfacesDiv(ticker, unique_ytes, strikes_yte, call_vals, put_vals);
        };
    }else{
        alert("Please select a .csv file");
    }
}