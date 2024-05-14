document.getElementById('reviewForm').onsubmit = function(event) {
    event.preventDefault();
    const reviewText = document.getElementById('reviewText').value;
    const aircraftType = document.getElementById('aircraftType').value;
    const route = document.getElementById('route').value;
    const resultElement = document.getElementById('result');
    const submitButton = document.querySelector('button[type="submit"]');

    submitButton.disabled = true;
    resultElement.innerText = 'Analyzing...';
    resultElement.className = 'text-info';

    sendRequest(1);

    function sendRequest(attempt) {
        fetch('/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text: reviewText, aircraftType: aircraftType, route: route})
        }).then(response => {
            if (!response.ok) throw new Error('Server responded with an error!');
            return response.json();
        }).then(data => {
            resultElement.innerText = 'Sentiment: ' + data.sentiment;
            resultElement.className = 'text-success';
            updateTable(data, reviewText, aircraftType, route);
            submitButton.disabled = false;
        }).catch(error => {
            resultElement.innerText = 'Failed after ' + attempt + ' attempts. Please check your network and try again.';
            resultElement.className = 'text-danger';
            if (attempt < 3) {
                setTimeout(() => sendRequest(attempt + 1), 2000);
            } else {
                submitButton.disabled = false;
            }
        });
    }
};

function updateTable(data, reviewText, aircraftType, route) {
    const tableBody = document.getElementById('reviewTable');
    const newRow = tableBody.insertRow();
    newRow.insertCell(0).innerText = data.reviewId;
    newRow.insertCell(1).innerText = aircraftType;
    newRow.insertCell(2).innerText = route;
    newRow.insertCell(3).innerText = reviewText;
    newRow.insertCell(4).innerText = data.sentiment;
}