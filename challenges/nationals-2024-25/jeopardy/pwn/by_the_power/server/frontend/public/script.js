document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed");

    const inputField = document.getElementById('inputString');
    console.log("Input Field Element:", inputField);

    const submitButton = document.getElementById('submitButton');
    console.log("Submit Button Element:", submitButton);

    const resultDisplay = document.getElementById('resultDisplay'); // Get the result display element

    if (submitButton) {
        submitButton.addEventListener('click', () => {
            if (inputField && resultDisplay) { // Check if resultDisplay exists
                const inputValue = inputField.value;
                fetch('http://10.0.2.61:8080/api/check-ssh-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    // inputValue: inputValue.replace(/\r?\n|\r/g, '').replace(/\s+/g, ''), // This line was incorrect and removed
                    body: JSON.stringify({ input:  inputValue.replace(/\r|\n/g, "")}),
                })
                .then(response => {
                    if (!response.ok) {
                        // Handle HTTP errors like 404 or 500
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json(); // This line was selected
                })
                .then(data => {
                    console.log('Success:', data);
                    // Display the data in the resultDisplay element
                    // Assuming data is an object with a 'message' property
                    resultDisplay.textContent = data.message || JSON.stringify(data);
                })
                .catch((error) => {
                    console.error('Error:', error);
                    // Display error message to the user
                    resultDisplay.textContent = `Error: ${error.message}`;
                });
            } else {
                if (!inputField) console.error("Input field not found!");
                if (!resultDisplay) console.error("Result display element not found!"); // Added check for resultDisplay
            }
        });
    } else {
        console.error("Submit button not found!");
    }
});