function getAvailableSlots(order_id) {
    fetch(`/get_available_slots/${order_id}`)
        .then(resp => resp.json())
        .then(data => {
            const slots = document.getElementById("slots-"+order_id);
            slots.innerHTML = '';
            data.forEach(slotElem => {
                const newSlot = document.createElement("option");
                newSlot.value = slotElem.id;
                newSlot.textContent = slotElem.elem;
                slots.appendChild(newSlot);
            });
        })
        .catch(e => console.error("Error when finding slots"));
}

