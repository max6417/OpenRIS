const form = document.getElementById("form-new-report");
const impressions = document.getElementById("impressions");
const findings = document.getElementById("findings")
const nbImpressionsWords = document.getElementById("nb-impressions-words");
const nbFindingsWords = document.getElementById("nb-findings-words");


impressions.addEventListener('input', () => {
   let words = impressions.value.trim();
   words = words ? words.split(/\s+/) : [];
   nbImpressionsWords.textContent = words.length;
});

findings.addEventListener('input', () => {
    let words = findings.value.trim();
    words = words ? words.split(/\s+/) : [];
    nbFindingsWords.textContent = words.length;
})



form.addEventListener("submit", (ev) => {
    let words = impressions.value.trim();
    words = words ? words.split(/\s+/) : [];

    if (words.length >= 500) {
        ev.preventDefault();
        alert("Impressions section should not exceed 500 words");
    }
});