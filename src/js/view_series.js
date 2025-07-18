function getSeriesUrl(series_id) {
    fetch(`/view_series/${series_id}`)
        .then(resp => resp.json())
        .then(data => {
            window.open(data.url, '_blank');
        })
        .catch(e => console.error(`Error when loading the web viewer`));
}