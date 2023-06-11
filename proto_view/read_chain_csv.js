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

function buildSurfaceImages(ticker, div){
    for(var i = 0; i < 18; i++){
        var img_header = document.createElement('h3');
        img_header.innerHTML = '$'+ticker+' Option Chain '+func_strs[i]+' & '+func_strs[i]+' Gradient Surfaces';
        div.appendChild(img_header);
        var img_elem = document.createElement('img');
        img_elem.src = 'png_outputs/chains/'+ticker+'_'+func_names[i]+'_quadsurface.png';
        div.appendChild(img_elem);
    }
}

function updateSurfacesDiv(ticker, div){
    if(!div.hasChildNodes()){
        buildSurfaceImages(ticker, div);
    }else{
        clearChildNodes(div);
        buildSurfaceImages(ticker, div);
    }
}

function readChainCSV(){
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
                for(var col = 0; col < col_data.length; col++){
                    var new_cell = new_row.insertCell();
                    if(col == 4){
                        new_cell.innerHTML = col_data[col]+' '+col_data[col+1];
                        col++;
                        continue;
                    }else{
                        new_cell.innerHTML = col_data[col];
                    }
                }
            }
            updateSurfacesDiv(ticker, document.getElementById('surfaces_area'));
        };
    }else{
        alert("Please select a .csv file");
    }
}