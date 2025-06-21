const draggable_list = document.getElementById('draggable-list');
const Summary_list = document.getElementById('summary')
const checkedItems = new Set();
localStorage.clear()
var checked_count
const questionItems = new Array();
const listItems = [];
var checkboxes

fetch('/cartView', {
        method: "POST",
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    })
    .then(response => response.json())
    .then(data => {
        data.forEach(item => {
            questionItems.push(item)
        });
        populateCart(data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });


// Function to populate cart with items selected from the questions section before
function populateCart(data) {
    getCartCount();

    console.log(questionItems)

    data.forEach((item, index) => {
        const listItem = document.createElement('li')
        listItem.setAttribute('data-index', index);

        listItem.innerHTML = `
        <div class='draggable' draggable='true' id='list-item-${item.id}'>
            <div class="item-wrapper d-flex align-items-center justify-content-between bg-body-tertiary p-2 rounded mb-2">
                <div class="checkbox p-2 me-2">
                    <input type="checkbox" class="form-check-input flex-shrink-0" id="${item.id}" name="checkbox-cart" value="${item.id}" checked>
                </div>
                <div class="flex-grow-1 p-2 me-2">
                    <div class="card mb-0">
                        <div class="row g-0 align-items-center">
                            <div class="col-md-12 col-12">
                                <div class="card-body p-2">
                                    <h5 class="card-title mb-1">${item.title}</h5>
                                    <p class="card-text d-none" data-user-card-text></p>
                                    <p class="card-text mb-0"><small class="text-body-secondary">${item.path}</small></p>
                                    <p class="card-text mb-0"><small class="text-body-secondary">${item.level}</small></p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="button p-2">
                    <button type="button" class="btn btn-danger modal-btn" data-bs-toggle="modal" data-bs-target="#modal-${item.id}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash3" viewBox="0 0 16 16">
                            <path d="M6.5 1h3a.5.5 0 0 1 .5.5v1H6v-1a.5.5 0 0 1 .5-.5M11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3A1.5 1.5 0 0 0 5 1.5v1H1.5a.5.5 0 0 0 0 1h.538l.853 10.66A2 2 0 0 0 4.885 16h6.23a2 2 0 0 0 1.994-1.84l.853-10.66h.538a.5.5 0 0 0 0-1zm1.958 1-.846 10.58a1 1 0 0 1-.997.92h-6.23a1 1 0 0 1-.997-.92L3.042 3.5zm-7.487 1a.5.5 0 0 1 .528.47l.5 8.5a.5.5 0 0 1-.998.06L5 5.03a.5.5 0 0 1 .47-.53Zm5.058 0a.5.5 0 0 1 .47.53l-.5 8.5a.5.5 0 1 1-.998-.06l.5-8.5a.5.5 0 0 1 .528-.47M8 4.5a.5.5 0 0 1 .5.5v8.5a.5.5 0 0 1-1 0V5a.5.5 0 0 1 .5-.5"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <div class="modal fade" id="modal-${item.id}" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="exampleModalLabel">Remove</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <span>Are you sure you want to remove the question from the cart?</span>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-danger removal" data-bs-dismiss="modal" value="${item.id}">Remove</button>
                    </div>
                </div>
            </div>
        </div>
        `

        listItems.push(listItem);
        draggable_list.appendChild(listItem);
    });

    addEventListeners();

    let rem = document.getElementsByClassName('removal');
    for (let i = 0; i < rem.length; i++) {
        rem[i].addEventListener("click", (e) => {
            const itemId = rem[i].value;
            removeItem(itemId);
        });
    }
    addCheckBoxListener();
    addSummary();

}

// Adding Event listeners to checkboxes for updating items selected count and exporting feature
function addCheckBoxListener() {
    checkboxes = document.querySelectorAll('.form-check-input');
    checked_count = checkboxes.length
    document.querySelector('[export-data]').textContent = `Items Selected: ${checked_count}`

    checkboxes.forEach(checkbox => {
        checkedItems.add(checkbox.value)
        checkbox.addEventListener("click", e => {
            if (checkbox.checked) {
                checked_count++
                checkedItems.add(checkbox.value)
            }
            else {
                checked_count--
                checkedItems.delete(checkbox.value)
            }
            document.querySelector('[export-data]').textContent = `Items Selected: ${checked_count}`
        })
    })
}

function addSummary() {
    fetch('/getSummary', {
        method: "POST",
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    })
    .then(response => response.json())
    .then(counts => {
        const Summary_list = document.getElementById('summary-list');
        Summary_list.innerHTML = ''; // Clear any existing items in the summary list

        Object.entries(counts).forEach(([level, count]) => {
            const listItem = document.createElement('li');
            listItem.innerHTML = `<p>${level}'s -> ${count}</p>`;
            Summary_list.appendChild(listItem);
        });
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function addEventListeners() {
    const draggables = document.querySelectorAll('.draggable');
    const dragListItems = document.querySelectorAll('.draggable-list li');
  
    draggables.forEach(draggable => {
      draggable.addEventListener('dragstart', dragStart);
    });
  
    dragListItems.forEach(item => {
      item.addEventListener('dragover', dragOver);
      item.addEventListener('drop', dragDrop);
      item.addEventListener('dragenter', dragEnter);
      item.addEventListener('dragleave', dragLeave);
    });
}

function dragStart() {
    // console.log('Event: ', 'dragstart');
    dragStartIndex = +this.closest('li').getAttribute('data-index');
}
  
function dragEnter() {
    // console.log('Event: ', 'dragenter');
    this.classList.add('over');
}

function dragLeave() {
    // console.log('Event: ', 'dragleave');
    this.classList.remove('over');
}

function dragOver(e) {
    // console.log('Event: ', 'dragover');
    e.preventDefault();
}

function dragDrop() {
    // console.log('Event: ', 'drop');
    const dragEndIndex = +this.getAttribute('data-index');
    swapItems(dragStartIndex, dragEndIndex);

    this.classList.remove('over');
}

// Swap list items that are drag and drop
function swapItems(fromIndex, toIndex) {
    const temp = listItems[fromIndex];
    listItems[fromIndex] = listItems[toIndex];
    listItems[toIndex] = temp;

    const itemOne = listItems[fromIndex].querySelector('.draggable');
    const itemTwo = listItems[toIndex].querySelector('.draggable');
  
    listItems[fromIndex].appendChild(itemTwo);
    listItems[toIndex].appendChild(itemOne);
}
  

function deselect_all() {
    let checkboxes = document.getElementsByClassName('form-check-input');
    console.log("test")
    for (let i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked) {
            checkedItems.delete(checkboxes[i].value)
            checkboxes[i].checked = false
        }
    }
    document.querySelector('[export-data]').textContent = `Items Selected: ${checkedItems.size}`
    checked_count = 0
}

// Function to dynamically remove item from cart
function removeItem(itemId) {
    // Implement the item removal logic, e.g., send a request to the server
    if (checkedItems.has(itemId)) {
        checkedItems.delete(itemId)
        document.querySelector('[export-data]').textContent = `Items Selected: ${checkedItems.size}`
    }
    var body = {
        id: itemId
    }
    fetch('/removeItem', {
        method: "POST",
        body: JSON.stringify(body),
        cache: "no-cache",
        headers: new Headers({
        "content-type": "application/json"
        })
    })
    .then(response => response.json())
    .then(data => {
        const cartCountElement = document.getElementById('cart-count');
        cartCountElement.textContent = data.cart_count;
        const itemElement = document.getElementById(`list-item-${itemId}`);
        itemElement.remove();
        getCartCount();
        addSummary();
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function remove_all() {
    checkedItems.forEach(item => {
        removeItem(item);
    })
}

function exporting(destination) {
    const form = document.createElement('form');
    form.action = '/exporting';
    form.method = 'post';
    form.target = '_blank';

    const data = new Array()
    const items = document.querySelectorAll('.form-check-input')
    items.forEach(item => {
        if (checkedItems.has(item.value)) {
            data.push(item.value)
        }
    });

    const fields = {
        dest: destination,
        data: JSON.stringify(data)
    };

    for (const [key, value] of Object.entries(fields)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = value;
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
}

document.querySelector('.export-doc-btn').addEventListener('click', () => exporting('doc'));
document.querySelector('.export-forms-btn').addEventListener('click', () => exporting('forms'));
