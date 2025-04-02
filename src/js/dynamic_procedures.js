function loadProcedure(modality) {
    fetch(`/get_procedures/${modality}`)
        .then(resp => resp.json())
        .then(data => {
            const procedures = document.getElementById('procedure');
            procedures.innerHTML = '';
            data.forEach(proc => {
                const newProc = document.createElement('option');
                newProc.value = proc._id;
                newProc.textContent = proc.name;
                procedures.appendChild(newProc);
            });
        })
        .catch(e => console.error("Error when loading procedures for ", modality, e));
}


document.getElementById("imaging_modality").addEventListener('change', () => {
    // TODO - Verify this function and fix it !
    const modality = document.getElementById("imaging_modality").value;
    if (modality) loadProcedure(modality);
});