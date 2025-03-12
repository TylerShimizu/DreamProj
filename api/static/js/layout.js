let questionData = {};

function getCartCount() {
    fetch('/getCartSize', {
        method: "POST",
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    })
    .then(response => response.json())
    .then(data => {
        const cartCountElement = document.getElementById('cart-count');
        cartCountElement.textContent = String(data.cart_count);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function SearchQuery() {
    fetch('/getData', {
        method: "POST",
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    })
    .then(response => response.json())
    .then(data => {
        questionData = data;
        console.log(questionData)

        const searchQueryStr = getQueryParam("searchQuery");
        if (searchQueryStr !== null) {
            console.log("test")
            searchBar.setAttribute("value", searchQueryStr)
            const filteredQuestions = questionData.filter(question => {
                return Object.values(question).some(field =>
                    field.toString().toLowerCase().includes(searchQueryStr)
                );
            });
            displayQuestions(filteredQuestions);
        } else {
            displayQuestions(questionData);
        }
    });
}

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

// Function to display questions
function displayQuestions(questions) {
    const resultsContainer = document.querySelector("#search-results"); // Assuming you have a container to display the results
    resultsContainer.innerHTML = ''; // Clear previous results

    if (questions.length === 0) {
        // If no questions match, display "No results found" message
        const noResults = document.createElement('p');
        noResults.classList.add('text-center', 'text-muted');
        noResults.textContent = 'No results found';
        resultsContainer.appendChild(noResults);
        return; // Stop further execution
    }

    questions.forEach(question => {
        // Create a new div element for the card
        const cardDiv = document.createElement('div');
        cardDiv.classList.add('col');

        // Define the card HTML structure
        cardDiv.innerHTML = `
            <div class="card h-100 border-dark mb-3">
                <div class="card-header bg-primary-subtle">${question['Category']} - ${question['Sub-Category']}</div>
                <div class="card-body">
                    <h5 class="card-title">${question['Item Stem']}</h5>
                </div>
                <div class="card-footer bg-warning-subtle">
                    <small class="text-muted">${question['Levels']}</small>
                    <a href="#" class="btn btn-warning stretched-link float-end" data-bs-toggle="modal" data-bs-target="#Modal-${question['id']}">More Info</a>
                </div>
            </div>

            <!-- Modal HTML -->
            <div class="modal fade" id="Modal-${question['id']}" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-scrollable">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h1 class="modal-title fs-5" id="exampleModalLabel">Add question to survey?</h1>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <h5>Question: <br> ${question['Item Stem']}</h5>
                            <br>
                            <p class="text-secondary">Anchor:
                                <ul>
                                    ${question['Anchors'].split(';').map(item => `<li class="text-secondary">${item}</li>`).join('')}
                                </ul>
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-warning" name="addCart-${question['id']}" data-bs-dismiss="modal" onclick="add_to_cart('${question['id']}')" value="${question['id']}">Add to Cart</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Append the card to the results container
        resultsContainer.appendChild(cardDiv);
    });
}

function searchQueryList(questions) {
    const searchBar = document.getElementById("search-bar");
    const searchResults = document.getElementById("searchRes");

    // Clear previous results
    searchResults.innerHTML = "";

    if (!questions) {
        searchResults.style.display = "none"
        return;
    }
    // Filter and sort options based on input
    const filteredOptions = questions;

    // Populate dropdown with filtered options
    if (filteredOptions.length > 0) {
        filteredOptions.forEach(option => {
            const li = document.createElement("li");
            li.classList.add("dropdown-item");
            li.textContent = option['Item Stem'];

            // Add click handler to populate search bar when an item is clicked
            li.addEventListener("click", () => {
                searchBar.value = option['Item Stem'];
                searchResults.innerHTML = ""; // Clear dropdown
            });

            searchResults.appendChild(li);
        });
        searchResults.style.display = "block";
    } else {
        searchResults.style.display = "none";
    }

    // Hide dropdown when clicking outside
    document.addEventListener("click", (e) => {
        if (!searchBar.contains(e.target)) {
            searchResults.style.display = "none";
        }
    });
}

// Event listener for the search bar
const searchBar = document.querySelector(".searchBar");
const searchQueryStr = getQueryParam("searchQuery");

searchBar.addEventListener("input", e => {
    const value = e.target.value.trim().toLowerCase();


    if (!value) {
        if (searchBar.getAttribute('name') === 'searchQuery') {
            searchQueryList(null)
        } else {
            // If the search input is empty, display all questions
            displayQuestions(questionData);
        }

    } else {
        // Filter questions based on input
        const filteredQuestions = questionData.filter(question => {
            return Object.values(question).some(field =>
                field.toString().toLowerCase().includes(value)
            );
        });
        if (searchBar.getAttribute('name') === 'searchQuery') {
            searchQueryList(filteredQuestions)
        } else {
            displayQuestions(filteredQuestions);
        }
    }
});