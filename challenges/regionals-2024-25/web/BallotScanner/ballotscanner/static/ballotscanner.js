qs = (s, d=document) => d.querySelector(s)
qsa = (s, d=document) => d.querySelectorAll(s)

function haltEvents(evt) {
    evt.preventDefault()
    evt.stopPropagation()
    evt.cancelBubble = true
}


function selectBallotImage(evt) {
    haltEvents(evt)

    qs("#ballotimage").click()
}


function enableProcessButton(evt) {
    haltEvents(evt)

    let selBtn = qs("#fileselect")

    qs("#submit").removeAttribute("disabled")
    selBtn.setAttribute("disabled","")
    selBtn.innerText = qs("#ballotimage").files[0].name
}


function scanBallot(evt) {
    haltEvents(evt)

    const xhr = new XMLHttpRequest();
    const form = new FormData();

    xhr.open("POST", "/scan", true);
    xhr.onreadystatechange = () => {
        if (xhr.readyState === xhr.DONE) {
            if (! xhr.responseURL.endsWith("/scan")) {
                window.location.href = xhr.responseURL
            } else {
                processResponse(xhr)
            } 
        }
        
    }

    form.append("ballotimage", qs("#ballotimage").files[0])

    xhr.send(form)
}


function processResponse(xhr) {
    let messages = qs("#messages")
    let selBtn = qs("#fileselect")
    selBtn.removeAttribute("disabled")
    selBtn.innerText = "Select Image..."

    if (xhr.status >= 400 ) {
        messages.classList.add("error")
        if (xhr.responseText !== "") {
            let jsResponse = JSON.parse(xhr.responseText)
            let errorMessage = jsResponse['err']
            messages.innerText = `Error: ${errorMessage}`
        } else {
            messages.innerText = `Unexpected error: ${xhr.status}`
        }
    } else {
        qs("#ballotimage").value = ""
        let json = JSON.parse(xhr.responseText)
        messages.innerHTML = ""
        let pre = document.createElement("pre")
        pre.innerText = json['msg'] + "\n\n"
        messages.appendChild(pre)
        messages.classList.remove("error")
    }
}


function isReady() {
    qs("#fileselect").addEventListener("click", selectBallotImage)
    qs("#submit").addEventListener("click", scanBallot)
    qs("#ballotimage").addEventListener("change", enableProcessButton)
}


window.addEventListener("DOMContentLoaded", isReady)