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

function getColor(value) {
    switch (value) {
        case 1: return "red";
        case 2: return "orange";
        case 3: return "yellow";
        case 4: return "lightgreen";
        case 5: return "green";
        default: return "#e0e0e0";
    }
}

function createGauge(id, label, value) {
    const gauge = new JustGage({
        id: id,
        value: value,
        min: 1,
        max: 5,
        gaugeColor: "#e0e0e0",
        levelColors: [getColor(value)],
        pointer: true,
        hideInnerShadow: true,
        animationSpeed: 20,
        label: label,
        labelFontColor: "#000000"
    });
}

function resubmit() {
    let code = $('#code-editor').val();

    $.ajax({
        type: "POST",
        url: "/resubmit_answer",
        data: JSON.stringify({ code: code }),
        processData: false,
        contentType: "application/json",
        beforeSend: function () { 
            $("#spinner-div").show()
        },
        success: function(response) {
            console.log(response);
            session_data = response;
            adjustFeedbackHeight();
            checkScores();
            updateResubmitButtonText(session_data.clarity_score);
            $('#feedback-content').html(`
                <p class="hover-txt"><b>Hover</b> over your scores too see feedback on how you can improve them!</p>
                <p class="score-txt">Score <b>at least 4</b> in each area to pass. You will receive <b>code hints</b> after your next submission.</p>
                <p class="instructions-txt">In your program, assume ./data.csv contains the data. You may import matplotlib, seaborn, and/or pandas. Hit 'CTRL + ENTER' while the editor is selected to try executing your code before submission.</p>
                `)
        },
        error: function(request, status, error) {
            console.log("Error resubmitting problem: ", error);
        },
        complete: function () { 
            $("#spinner-div").hide();
        }
    });
}

function adjustFeedbackHeight() {

    createGauge("gauge-clarity", "Clarity", session_data.clarity_score);
    createGauge("gauge-accuracy", "Accuracy", session_data.accuracy_score);
    createGauge("gauge-depth", "Depth", session_data.depth_score);

    let butColHeight = $('#score-content').outerHeight(true);
    $('.feedback-content').css('height', `calc(100vh - ${70 + 100 + butColHeight}px)`);
    
}

function cleanInput(input) {

    if (input.startsWith('"') && input.endsWith('"')) {
        input = input.slice(1, -1);
    }

    return input.split('\\n').map(line => line.trim()).filter(line => line !== '');
}

function formatDiff(original, modified) {

    const originalLines = cleanInput(original);
    const modifiedLines = cleanInput(modified);
    let formattedDiff = '';

    for (let i = 0; i < originalLines.length - 1; i++) {
        const originalLine = originalLines[i];
        if (!(originalLine.includes("NONE") || originalLine.length == 0)) {
            formattedDiff += `<div class="line removed hoverable-line">- ${originalLine}</div>\n`;
        }
    }

    formattedDiff += `<br>`;

    for (let i = 0; i < modifiedLines.length - 1; i++) {
        const modifiedLine = modifiedLines[i];
        if (!(modifiedLine.includes("NONE") || modifiedLine.length === 0)) {
            formattedDiff += `<div class="line added">+ ${modifiedLine}</div>\n`;
        }
    }

    // for (let i = 0; i < Math.max(originalLines.length, modifiedLines.length); i++) {
    //     const originalLine = originalLines[i] || '';
    //     const modifiedLine = modifiedLines[i] || '';

    //     if (originalLine === modifiedLine) {
    //         // Same lines
    //         formattedDiff += `<div class="line same">${originalLine}</div>\n`;
    //     } else if (!originalLine) {
    //         // New line added
    //         formattedDiff += `<div class="line added">+ ${modifiedLine}</div>\n`;
    //     } else if (!modifiedLine) {
    //         // Line removed
    //         formattedDiff += `<div class="line removed">- ${originalLine}</div>\n`;
    //     } else {
    //         // Line modified
    //         formattedDiff += `<div class="line removed">- ${originalLine}</div>\n`;
    //         formattedDiff += `<div class="line added">+ ${modifiedLine}</div>\n`;
    //     }
    // }

    $('.diff-viewer').append(formattedDiff);
}

function checkScores() {
    if (session_data.clarity_score >= 4 && session_data.accuracy_score >= 4 && session_data.depth_score >= 4) {
        $('#complete-btn').prop('disabled', false);
    } else {
        $('#complete-btn').prop('disabled', true);
    }
}

function vote(voteType) {
    // Handle the vote (upvote or downvote)
    if (voteType === 'up') {
        updateLikes(session_data['id'], 1);
    } else if (voteType === 'down') {
        updateLikes(session_data['id'], -1);
    } 
    
    // Close the modal after voting
    closeModal();
    window.location.href = `/`;
}

function complete() {
    document.getElementById("voteModal").style.display = "block";
    // window.location.href = `/`;
}

function closeModal() {
    // Close the modal when the user clicks the close button
    document.getElementById("voteModal").style.display = "none";
}

function executeCode() {
    let id = session_data.id;
    let code = $('#code-editor').val();
    code = code.replace(/\S*data\.csv\S*/g, "dataset");
    $.ajax({
        type: "POST",
        url: "/execute_code",
        data: JSON.stringify({ id: id, code: code }),
        processData: false,
        contentType: "application/json",
        success: function(response) {
            $('#executeModal').show();
            $('#execText').empty();

            console.log(response);

            $('#imageContainer').attr('src', "");
            $('#imageContainer').attr('alt', "Plot did not load correctly.");
            if (response.image) {
                let imageUrl = `data:image/png;base64,${response.image}`;
                $('#imageContainer').attr('src', imageUrl);
                $('#imageContainer').attr('alt', "Your plot.");
            }

            let printedOutput = response.output || "";  
            if (printedOutput) {
                $('#execText').prepend(`<pre>${printedOutput.replace(/\n/g, "<br>")}</pre>`);
            }
        },
        error: function(request, status, error) {
            console.log("Error executing code: ", error);
            $('#executeModal').show();
            $('#imageContainer').attr('src', "");
            $('#imageContainer').attr('alt', "Plot did not load correctly.");
            $('#execText').empty();
            let errorMessage = request.responseJSON.error || "An error occurred.";
            let traceback = request.responseJSON.traceback || "";
            let formattedError = `<pre>${errorMessage}\n${traceback.replace(/\n/g, "<br>")}</pre>`;
            $('#execText').html(formattedError);
        }
    });
}

function resetHoverables() {
    $('.hoverable-line').hover(function() {
        let codeToHighlight = $(this).text().replace(/-/g, '').trim();
        const codeEditor = $('#code-editor');
        const lines = codeEditor.val().split('\n');
        
        // Find the index of the line that contains the code to highlight
        const lineIndex = lines.findIndex(line => line.includes(codeToHighlight));
        
        if (lineIndex !== -1) {
            // Calculate the height of each line (adjust as needed)
            const lineHeight = parseInt(getComputedStyle(codeEditor[0]).lineHeight, 10);
            const scrollPosition = lineIndex * lineHeight;
    
            // Scroll the textarea to the desired position
            codeEditor.scrollTop(scrollPosition);
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
            window.location.href = `/`;
        },
        error: function(request, status, error) {
            console.log("Error updating likes: ", error);
        }
    });
  }

function updateResubmitButtonText(clarityScore) {
    if (clarityScore === 0) {
        $('#resubmit-btn').text('SUBMIT');
    } else {
        $('#resubmit-btn').text('RESUBMIT');
    }
}

/////////////////////////////////////////////////////////////////////////////////

function pageSetup() {
    console.log(session_data);

    var codeEditor = $('#code-editor');
    var cleanedCode = codeEditor.val().split('\n').map(function(line) {
        return line.trimStart();
    }).join('\n');
    codeEditor.val(cleanedCode);
    adjustFeedbackHeight();
    checkScores();

    updateResubmitButtonText(session_data.clarity_score);
}

$(window).resize(adjustFeedbackHeight);

$(document).ready(function() {

    pageSetup();

    const csvTable = csvToTable(session_data.dataset);
    $('#dataset-content').empty();
    $('#dataset-content').append(`${csvTable}`);

    $('#resubmit-btn').on('click', function() {
        resubmit();
    });

    $('#complete-btn').on('click', function() {
        complete();
    });

    $('#gauge-clarity').hover(
        function() {
            let feedbackContent = ``;
            if (session_data.clarity_score != 5 && (session_data.clarity_quote || session_data.clarity_diff)) {
                try {
                    feedbackContent = `<p class="suggestions">${session_data.clarity}</p><div class="diff-viewer"></div>`;
                    $('#feedback-content').html(feedbackContent);
                    formatDiff(session_data.clarity_quote.trim(), session_data.clarity_diff.trim());
                } catch {
                    feedbackContent = `${session_data.clarity}<br><br>`;
                    feedbackContent += `
                        ${session_data.clarity_quote}<br><br>
                        ${session_data.clarity_diff}
                    `;
                    $('#feedback-content').html(feedbackContent);
                }
            } else {
                $('#feedback-content').html(session_data.clarity);
            }
            $('#clarity-col').css('background-color', '#efffea');
            $('#accuracy-col').css('background-color', 'transparent');
            $('#depth-col').css('background-color', 'transparent');
            resetHoverables();
        }
    );

    $('#gauge-accuracy').hover(
        function() {
            let feedbackContent = ``;
            if (session_data.accuracy_score != 5 && (session_data.accuracy_quote || session_data.accuracy_diff)) {
                try {
                    feedbackContent = `<p class="suggestions">${session_data.accuracy}</p><div class="diff-viewer"></div>`;
                    $('#feedback-content').html(feedbackContent);
                    formatDiff(session_data.accuracy_quote.trim(), session_data.accuracy_diff.trim());
                } catch {
                    feedbackContent = `${session_data.accuracy}<br><br>`;
                    feedbackContent += `
                        ${session_data.accuracy_quote}<br><br>
                        ${session_data.accuracy_diff}
                    `;
                    $('#feedback-content').html(feedbackContent);
                }
            } else {
                $('#feedback-content').html(session_data.accuracy);
            }
            $('#clarity-col').css('background-color', 'transparent');
            $('#accuracy-col').css('background-color', '#efffea');
            $('#depth-col').css('background-color', 'transparent');
            resetHoverables();
        }
    );

    $('#gauge-depth').hover(
        function() {
            let feedbackContent = ``;
            if (session_data.depth_score != 5 && (session_data.depth_quote || session_data.depth_diff)) {
                try {
                    feedbackContent = `<p class="suggestions">${session_data.depth}</p><div class="diff-viewer"></div>`;
                    $('#feedback-content').html(feedbackContent);
                    formatDiff(session_data.depth_quote.trim(), session_data.depth_diff.trim());
                } catch {
                    feedbackContent = `${session_data.depth}<br><br>`;
                    feedbackContent += `
                        ${session_data.depth_quote}<br><br>
                        ${session_data.depth_diff}
                    `;
                    $('#feedback-content').html(feedbackContent);
                }
            } else {
                $('#feedback-content').html(session_data.depth);
            }
            $('#clarity-col').css('background-color', 'transparent');
            $('#accuracy-col').css('background-color', 'transparent');
            $('#depth-col').css('background-color', '#efffea');
            resetHoverables();
        }
    );

    $('.code-editor').on('keydown', function (event) {
        if (event.ctrlKey && event.key === 'Enter') {
            // Show the modal popup when CTRL + ENTER is pressed
            executeCode();
        }
    });

    $('#closeModal').on('click', function () {
        $('#executeModal').hide();
    });
    


});
