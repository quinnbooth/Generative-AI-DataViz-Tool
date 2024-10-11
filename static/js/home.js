function getProblems(select, id) {
    $.ajax({
        type: "POST",
        url: "/get_problems",
        data: JSON.stringify({}),
        processData: false,
        contentType: "application/json",
        success: function(response) {
            first_id = listProblems(response);
            if (select == 1) selectProblem(first_id);
            if (select != 1) selectProblem(id);
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
    $('#question-div').text(problem.question);
    $('#question-div').data("id", problem.id);
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

    $.ajax({
        type: "POST",
        url: "/generate_problem",
        data: JSON.stringify({ keywords: keywords }),
        processData: false,
        contentType: "application/json",
        success: function(response) {
            getProblems(0, response.entryno);
        },
        error: function(request, status, error) {
            console.log("Error generating problem: ", error);
        }
    });

}

function submitAnswer() {
    let answer = $('#code-editor').val();
    let id = $('#question-div').data("id");

    $.ajax({
        type: "POST",
        url: "/submit_answer",
        data: JSON.stringify({ id: id, answer: answer }),
        processData: false,
        contentType: "application/json",
        beforeSend: function () { 
            $("#spinner-div").show()
        },
        success: function(response) {
            feedbackPage(response, answer, id);
        },
        error: function(request, status, error) {
            console.log("Error submitting problem: ", error);
        },
        complete: function () { 
            $("#spinner-div").hide();
        }
    });

    // For testing:
    // feedbackPage({"msg": "hi", "clarity": "csdfadfsafdsldfjk", "accuracy": "asdjflaskdjf", "insightfulness": "ajsld;jfalskdjf;lasjdlf"});
}

function idealViz() {
    let answer = $('#code-editor').val();
    let id = $('#question-div').data("id");

    $.ajax({
        type: "POST",
        url: "/get_ideal_viz",
        data: JSON.stringify({ id: id, answer: answer }),
        processData: false,
        contentType: "application/json",
        beforeSend: function () { 
            $("#spinner-div").show()
        },
        success: function(response) {
            $('#feedbackContent').append(response.msg);
        },
        error: function(request, status, error) {
            console.log("Error getting ideal answer: ", error);
        },
        complete: function () { 
            $("#spinner-div").hide();
        }
    });
}

function feedbackPage(feedback, answer, id) {
    console.log(feedback.msg);
    $('#feedback').empty();
    $('#feedbackModal').show();
    $('#feedback').append(`<h5 style="color: #4CAF50; font-weight: bold;">Clarity:</h5><p>${feedback.clarity}</p>`);
    $('#feedback').append(`<h5 style="color: #4CAF50; font-weight: bold;">Accuracy:</h5><p>${feedback.accuracy}</p>`);
    $('#feedback').append(`<h5 style="color: #4CAF50; font-weight: bold;">Insightfulness:</h5><p>${feedback.insightfulness}</p>`);
    
}

$(document).ready(function() {
    
    $("#spinner-div").hide();
    getProblems(1, 0);

    $('.generate-button').on('click', function() {
        $('#generateModal').modal('show');
    });

    $('#submitButton').on('click', function() {
        const keywords = $('#dataField').val();
        $('#generateModal').modal('hide');
        getNewProblem(keywords);
    });

    $('.code-editor').on('keydown', function (event) {
        if (event.ctrlKey && event.key === 'Enter') {
            // Show the modal popup when CTRL + ENTER is pressed
            $('#popupModal').show();
        }
    });

    $('#submit-btn').on('click', function() {
        submitAnswer();
    });

    $('#closeModal').on('click', function () {
        $('#popupModal').hide();
    });

    $('#closeFeedbackModal').on('click', function () {
        $('#feedbackModal').hide();
    });

    $('#feedbackModal').draggable({
        handle: '#draggableBar'
    });

    $('#seeIdealBtn').on('click', function () {
        idealViz();
    });
    
});
