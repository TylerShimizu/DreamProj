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
    });
}

function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
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
                const stem = encodeURIComponent(option['Item Stem']);
                window.location.href = `/questions?search=${option['Item Stem']}`;
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
const urlParams = new URLSearchParams(window.location.search);
const searchValue = urlParams.get("searchQuery");


document.addEventListener("DOMContentLoaded", () => {
    searchBar.addEventListener("input", (e) => {
        const value = e.target.value.trim().toLowerCase();
        console.log(value)
    
        if (!value) {
            if (searchBar.getAttribute('name') === 'searchQuery') {
                searchQueryList(null)
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
            }
        }
    });
});

// If it exists, populate the search bar
if (searchValue) {
    if (searchBar) {
        searchBar.value = decodeURIComponent(searchValue);
        const filteredQuestions = questionData.filter(question => {
            return Object.values(question).some(field =>
                field.toString().toLowerCase().includes(searchBar.value)
            );
        });
        if (searchBar.getAttribute('name') !== 'searchQuery') {
            displayQuestions(filteredQuestions);
        }
    }
};