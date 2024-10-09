function getProblems(select) {
    $.ajax({
        type: "POST",
        url: "/get_problems",
        data: JSON.stringify({}),
        processData: false,
        contentType: "application/json",
        success: function(response) {
            first_id = listProblems(response);
            if (select) selectProblem(first_id);
        },
        error: function(request, status, error) {
            console.log("Error getting problem list: ", error);
        }
    });
}

function updateLikes(entry, inc) {
    $.ajax({
        type: "POST",
        url: "/update_likes",
        data: JSON.stringify({ id: entry, increment: inc }),
        processData: false,
        contentType: "application/json",
        success: function(response) {
            listProblems(response);
        },
        error: function(request, status, error) {
            console.log("Error updating likes: ", error);
        }
    });
}

function selectProblem(id) {
    $('.entry').removeClass('entryToggle');
    $(`#entry-${id}`).toggleClass('entryToggle');

    $.ajax({
        type: "POST",
        url: "/get_problem",
        data: JSON.stringify({ id: id }),
        processData: false,
        contentType: "application/json",
        success: function(response) {
            displayProblem(response);
        },
        error: function(request, status, error) {
            console.log("Error getting problem: ", error);
        }
    });
}

function displayProblem(problem) {
    console.log(problem);
    const csvTable = csvToTable(problem.dataset);
    $('#csv-container').empty();
    $('#csv-container').append(`
        ${csvTable}
    `);
}

function csvToTable(csv) {
    const rows = csv.trim().split('\n');
    let table = '<table class="csv-table"><thead><tr>';
    const headers = rows[0].split(',');
    headers.forEach(header => {
        table += `<th>${header.trim()}</th>`;
    });
    table += '</tr></thead><tbody>';
    for (let i = 1; i < rows.length; i++) {
        if (rows[i].trim() === '') continue;
        const cells = rows[i].split(',');
        table += '<tr>';
        cells.forEach(cell => {
            table += `<td>${cell.trim()}</td>`;
        });
        table += '</tr>';
    }
    table += '</tbody></table>';
    return table;
}

function listProblems(entries) {
        
    entries.sort((a, b) => b.likes - a.likes);

    const entriesContainer = $('#entries-container');
    entriesContainer.empty();

    let mostLikedEntryId = null;
    let maxLikes = -1;

    entries.forEach(entry => {
        const entryDiv = $(`<div class="entry" id="entry-${entry.id}"></div>`);
        entryDiv.html(`
            <h4>${entry.question}</h4>
            <div class="entry-footer">
                <button class="upvote-button" id="upvote-${entry.id}">
                    <i class="fas fa-arrow-up"></i>
                </button>
                <div class="like-count" id="like-count-${entry.id}">${entry.likes}</div>
                <button class="downvote-button" id="downvote-${entry.id}">
                    <i class="fas fa-arrow-down"></i>
                </button>
            </div>
        `);

        entriesContainer.append(entryDiv);

        $(`#upvote-${entry.id}`).on('click', function(e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            updateLikes(entry.id, 1)
        });
        $(`#downvote-${entry.id}`).on('click', function(e) {
            e.preventDefault();
            e.stopImmediatePropagation();
            updateLikes(entry.id, -1)
        });
        $(`#entry-${entry.id}`).on('click', () => selectProblem(entry.id))
 
        if (entry.likes > maxLikes) {
            maxLikes = entry.likes;
            mostLikedEntryId = entry.id;
        }

    });

    return mostLikedEntryId

}

function getNewProblem(keywords) {
    console.log(keywords);

    let prompt = `
    Create one more entry for a json in the below form.
    Each should be accompanies by an interesting/difficult question that can be answered about the dataset using dataviz.
    The dataset should relate to the keywords ${keywords}.
    Think of diverse questions dataviz could be used to ask.
    
    Examples:
    {
        "id": 2,
        "dataset": "Product, Q1 Sales, Q2 Sales, Q3 Sales, Q4 Sales, Yearly Growth, Customer Satisfaction\nElectronics, 150000, 200000, 250000, 300000, 25%, 4.5\nClothing, 50000, 75000, 100000, 125000, 20%, 4.0\nGroceries, 100000, 150000, 200000, 250000, 15%, 4.8\nFurniture, 75000, 100000, 125000, 150000, 10%, 4.1\nToys, 40000, 60000, 90000, 120000, 30%, 4.6\nBooks, 30000, 45000, 70000, 90000, 18%, 4.3",
        "question": "What are the trends in sales across different product categories, and how do these trends correlate with customer satisfaction?",
        "likes": 6
    },
    {
        "id": 3,
        "dataset": "Year, Active Users, New Users, Churn Rate, Revenue, Cost of Acquisition\n2020, 5000, 2000, 5%, 20000, 5000\n2021, 7000, 3000, 4%, 30000, 7000\n2022, 12000, 5000, 6%, 45000, 10000\n2023, 15000, 6000, 3%, 60000, 8000\n2024, 18000, 8000, 2%, 75000, 9000\n2025, 21000, 10000, 1%, 90000, 11000",
        "question": "How has user growth evolved over the years, and what patterns can be identified in user acquisition costs and churn rates?",
        "likes": 7
    },
    {
        "id": 4,
        "dataset": "Date, Temperature, Sales, Customer Traffic, Conversion Rate\n2023-01-01, 30, 1500, 300, 5%\n2023-01-02, 32, 1600, 320, 5.5%\n2023-01-03, 35, 1700, 350, 6%\n2023-01-04, 28, 1400, 280, 4.5%\n2023-01-05, 25, 1300, 250, 4%\n2023-01-06, 40, 2000, 400, 7%\n2023-01-07, 38, 1900, 390, 6.5%\n2023-01-08, 29, 1550, 310, 5.2%",
        "question": "What patterns emerge between temperature changes and customer traffic throughout the week, and how do they affect sales?",
        "likes": 4
    }
        `


}

$(document).ready(function() {
    
    getProblems(1);

    $('.generate-button').on('click', function() {
        $('#generateModal').modal('show');
    });

    $('#submitButton').on('click', function() {
        const keywords = $('#dataField').val();
        $('#generateModal').modal('hide');
        getNewProblem(keywords);
    });
    
});
