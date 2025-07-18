function fetchSlots(patient_id) {
    let proc_id = document.getElementById("procedure").value;
    const button = document.getElementById("register-order-button");
    fetch(`/schedule/${patient_id}/${proc_id}`)
        .then(resp => resp.json())
        .then(data => {
            const slots = document.getElementById("slots");
            slots.innerHTML = '';
            data.forEach(slotElem => {
               const newSlot = document.createElement("option");
               newSlot.value = slotElem.id;
               newSlot.textContent = slotElem.elem;
               slots.appendChild(newSlot)
            });
        })
        .catch(e => console.error("Error when finding slots"));
    button.disabled = false;
}

document.getElementById("procedure").addEventListener('change', () => {
    const slots = document.getElementById("slots");
    const button = document.getElementById("register-order-button");
    slots.innerHTML = "";    // If we change the current modality in the form, we have to recompute all the possible slots (not the same duration)
    button.disabled = true;    // If we change the procedure, we have to recompute the available slots
});

document.getElementById("imaging_modality").addEventListener('change', () => {
    const slots = document.getElementById("slots");
    const button = document.getElementById("register-order-button");
    slots.innerHTML = "";
    button.disabled = true;
});
