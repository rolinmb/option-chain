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

function clearChildNodes(div){
    while(div.firstChild){
        div.removeChild(div.firstChild);
    }
}

function updateSurfaceImages(ticker){
    var div = document.getElementById('surface_imgs');
    if(div.hasChildNodes()){ clearChildNodes(div); }
    for(var i = 0; i < 18; i++){
        var img_header = document.createElement('h3');
        img_header.innerHTML = '$'+ticker+' Option Chain '+func_strs[i]+' & '+func_strs[i]+' Gradient Surfaces';
        div.appendChild(img_header);
        var img_elem = document.createElement('img');
        img_elem.src = '../png_outputs/chains/'+ticker+'_'+func_names[i]+'_quadsurface.png';
        div.appendChild(img_elem);
    }
}

function updateIndividualPlots(ticker, ytes, strikes, call_df, put_df, fresh){
    var call_div = document.getElementById('call_surfaces');
    var put_div = document.getElementById('put_surfaces');
    if(fresh){ // Create new children plots of call/put surfaces containers
        for(const key in call_df){
            var c_layout = { title: ticker+' Call '+key, autosize: false, width: 750, height: 750 };
            var p_layout = { title: ticker+' Put '+key, autosize: false, width: 750, height: 750 };
            var new_call_elmnt = document.createElement('div');
            var c_data = [{
                type: 'surface',
                colorscale: 'Electric',
                x: strikes,
                y: ytes,
                z: call_df[key]
            }];
            new_call_elmnt.id = 'call_'+key;
            call_div.appendChild(new_call_elmnt);
            Plotly.plot(document.getElementById('call_'+key), c_data, c_layout);
            var p_data = [{
                type: 'surface',
                colorscale: 'Electric',
                x: strikes,
                y: ytes,
                z: put_df[key]
            }];
            var new_put_elmnt = document.createElement('div');
            new_put_elmnt.id =  'put_'+key;
            put_div.appendChild(new_put_elmnt);
            Plotly.plot(document.getElementById('put_'+key), p_data, p_layout);
        }
    }else{ // Get children plot divs of main call/put surfaces containers and update
        var c_children = call_div.children;
        var p_children = put_div.children;
        const data_keys = call_df.keys();
        for(let i = 0; i < c_children.length; i++){
            var c_layout = { title: ticker+' Call '+data_keys[i], autosize: false, width: 700, height: 700 };
            var p_layout = { title: ticker+' Put '+data_keys[i], autosize: false, width: 700, height: 700 };
            var c_data = [{
                type: 'surface',
                colorscale: 'Electric',
                x: strikes,
                y: ytes,
                z: call_df[keys[i]]
            }];
            var p_data = [{
                type: 'surface',
                colorscale: 'Electric',
                x: strikes,
                y: ytes,
                z: put_df[keys[i]]
            }];
            Plotly.newPlot(c_children[i], c_data, c_layout);
            Plotly.newPlot(p_children[i], p_data, p_layout);
        }
    }
}

function updateSurfaces(ticker, ytes, strikes, call_df, put_df){
    console.log('Length of ytes List:',ytes.length);
    console.log('Length of strikes List (should match ytes):',strikes.length);
    console.log('Length of Call IV Value List (should match ytes):',call_df['iv'].length);
    console.log('Length of Put IV Value List (should match ytes):',put_df['iv'].length);
    if(!document.getElementById('surface_imgs').hasChildNodes()){
        updateIndividualPlots(ticker, ytes, strikes, call_df, put_df, true); // Create new plot divs; fresh=true
    }else{
        updateIndividualPlots(ticker, ytes, strikes, call_df, put_df, false); // Update existing divs; fresh=false
    }
    updateSurfaceImages(ticker);
}

function readChainCSV(){
    var unique_ytes = [];
    var strikes_yte = []; // list of lists
    var call_df = { // each key-value is a list of lists
        theo_dif: [],
        iv: [],
        mid_iv: [],
        delta: [],
        lambda: [],
        vega: [],
        rho: [],
        epsilon: [],
        theta: [],
        gamma: [],
        vanna: [],
        charm: [],
        vomma: [],
        veta: [],
        speed: [],
        zomma: [],
        color: [],
        ultima: []
    };
    var put_df = { // each key-value is a list of lists
        theo_dif: [],
        iv: [],
        mid_iv: [],
        delta: [],
        lambda: [],
        vega: [],
        rho: [],
        epsilon: [],
        theta: [],
        gamma: [],
        vanna: [],
        charm: [],
        vomma: [],
        veta: [],
        speed: [],
        zomma: [],
        color: [],
        ultima: []
    };
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
                    continue; // handles extra empty row being output at end of HTML table
                }
                // Detect new YTE/Expiration
                if(!unique_ytes.includes(col_data[3])){
                    exp_num++; // increment index/counter for building df's
                    unique_ytes.push(col_data[3]); // add YTE to unique_ytes
                    strikes_yte.push([]); // new strike list for each expiration
                    for(key in call_df){  // new calculations lists for each expiration
                        call_df[key].push([]);
                        put_df[key].push([]);
                    }
                }
                strikes_yte[exp_num-1].push(col_data[6]); // Unique strkes for YTE

                call_df['theo_dif'][exp_num-1].push(col_data[12]);
                call_df['iv'][exp_num-1].push(col_data[16]);
                call_df['mid_iv'][exp_num-1].push(col_data[17]);
                call_df['delta'][exp_num-1].push(col_data[18]);
                call_df['lambda'][exp_num-1].push(col_data[19]);
                call_df['vega'][exp_num-1].push(col_data[20]);
                call_df['rho'][exp_num-1].push(col_data[21]);
                call_df['epsilon'][exp_num-1].push(col_data[22]);
                call_df['theta'][exp_num-1].push(col_data[23]);
                call_df['gamma'][exp_num-1].push(col_data[24]);
                call_df['vanna'][exp_num-1].push(col_data[25]);
                call_df['charm'][exp_num-1].push(col_data[26]);
                call_df['vomma'][exp_num-1].push(col_data[27]);
                call_df['veta'][exp_num-1].push(col_data[28]);
                call_df['speed'][exp_num-1].push(col_data[29]);
                call_df['zomma'][exp_num-1].push(col_data[30]);
                call_df['color'][exp_num-1].push(col_data[31]);
                call_df['ultima'][exp_num-1].push(col_data[32]);

                put_df['theo_dif'][exp_num-1].push(col_data[38]);
                put_df['iv'][exp_num-1].push(col_data[42]);
                put_df['mid_iv'][exp_num-1].push(col_data[43]);
                put_df['delta'][exp_num-1].push(col_data[44]);
                put_df['lambda'][exp_num-1].push(col_data[45]);
                put_df['vega'][exp_num-1].push(col_data[46]);
                put_df['rho'][exp_num-1].push(col_data[47]);
                put_df['epsilon'][exp_num-1].push(col_data[48]);
                put_df['theta'][exp_num-1].push(col_data[49]);
                put_df['gamma'][exp_num-1].push(col_data[50]);
                put_df['vanna'][exp_num-1].push(col_data[51]);
                put_df['charm'][exp_num-1].push(col_data[52]);
                put_df['vomma'][exp_num-1].push(col_data[53]);
                put_df['veta'][exp_num-1].push(col_data[54]);
                put_df['speed'][exp_num-1].push(col_data[55]);
                put_df['zomma'][exp_num-1].push(col_data[56]);
                put_df['color'][exp_num-1].push(col_data[57]);
                put_df['ultima'][exp_num-1].push(col_data[58]);

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
            updateSurfaces(ticker, unique_ytes, strikes_yte, call_df, put_df);
        };
    }else{
        alert("Please select a .csv file");
    }
}