function tableSorting(tableId, columnIndex) {
    const table = document.getElementById(tableId);
    var rows, switching, i, x, y, hasToSwitch, direction, count = 0;
    switching = true;
    direction = "a"

    while (switching) {
        switching = false
        rows  = table.rows
        for (i = 1; i < (rows.length - 1); i++) {
            hasToSwitch = false;
            x = rows[i].getElementsByTagName("TD")[columnIndex];
            y = rows[i + 1].getElementsByTagName("TD")[columnIndex];
            if (direction === 'a') {
                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                    hasToSwitch = true;
                    break;
                }
            } else if (direction === 'd') {
                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                    hasToSwitch = true;
                    break;
                }
            }
        }
        if (hasToSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            count++;
        } else {
            if (count === 0 && direction === 'a') {
                direction = 'd';
                switching = true;
            }
        }
    }
}