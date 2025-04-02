document.addEventListener('DOMContentLoaded', () => {
    const datepicker = document.getElementById('examination_date-date');
    if (datepicker) {
        M.Datepicker.init(datepicker, {
            format: 'yyyy-mm-dd',
            minDate: new Date(),
            autoClose: true
        });
    }

    const patientBOD = document.getElementById('patient_dob');
    if (patientBOD) {
        M.Datepicker.init(patientBOD, {
            format: 'yyyy-mm-dd',
            maxDate: new Date(),
            autoClose: true,
            yearRange: 100
        });
    }

    const timepicker = document.querySelector('.exam-time');
    if (timepicker) {
        M.Timepicker.init(timepicker, {
            twelveHour: false,
            autoClose: true
        });
    }
});
