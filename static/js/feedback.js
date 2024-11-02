function csvToTable(csv) {
    const rows = csv.trim().split('\n');
    let table = '<table class="csv-table"><thead><tr>';
    const headers = rows[0].split(',');
    headers.forEach(header => {
        table += `<th>${header.trim()}</th>`;
    });
    table += '</tr></thead><tbody>';
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].trim() === '') continue;
        const cells = rows[i].split(',');
        table += '<tr>';
        cells.forEach(cell => {
            table += `<td>${cell.trim()}</td>`;
        });
        table += '</tr>';
    }
    table += '</tbody></table>';
    return table;
}

$(document).ready(function() {
    
    const csvTable = csvToTable(session_data.dataset);
    $('#dataset-content').empty();
    $('#dataset-content').append(`${csvTable}`);
    
});