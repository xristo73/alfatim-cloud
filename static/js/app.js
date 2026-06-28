console.log("window.currentPath =", window.currentPath);
document.addEventListener("DOMContentLoaded", function () {
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const relativePaths = document.getElementById("relative-paths");

dropZone.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", () => {

    let paths = [];

    for (let file of fileInput.files) {
        if (file.webkitRelativePath) {
            paths.push(file.webkitRelativePath);
        } else {
            paths.push(file.name);
        }
    }

    relativePaths.value = JSON.stringify(paths);
});

dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("bg-blue-100");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("bg-blue-100");
});

async function readEntry(entry, path = "") {

    let files = [];

    if (entry.isFile) {

        files.push(await new Promise(resolve => {
            entry.file(file => {
                file.fullPath = path + file.name;
                resolve(file);
            });
        }));

    } else if (entry.isDirectory) {

        const reader = entry.createReader();

        const entries = await new Promise(resolve => {
            reader.readEntries(resolve);
        });

        for (const e of entries) {
            files.push(...await readEntry(
                e,
                path + entry.name + "/"
            ));
        }
    }

    return files;
}

dropZone.addEventListener("drop", async (e) => {

    e.preventDefault();
    dropZone.classList.remove("bg-blue-100");

    let files = [];
    let paths = [];

    for (const item of e.dataTransfer.items) {

        const entry = item.webkitGetAsEntry();

        if (entry) {
            files.push(...await readEntry(entry));
        }
    }

    const dt = new DataTransfer();

    for (const file of files) {
        dt.items.add(file);
        paths.push(file.fullPath);
    }

    fileInput.files = dt.files;

    relativePaths.value = JSON.stringify(paths);

    console.log("DROP FILES:", files.length);
    console.log("DROP PATHS:", paths);
});

function renameItem(oldName) {

    let newName = prompt("Nowa nazwa:", oldName);

    if (!newName || newName === oldName)
        return;

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/rename";

    form.innerHTML = `
    <input type="hidden" name="current_path" value="${window.currentPath}">
    <input type="hidden" name="old_name" value="${oldName}">
    <input type="hidden" name="new_name" value="${newName}">
`;

    document.body.appendChild(form);
    form.submit();
}

const selectAll = document.getElementById("select-all");
const countBox = document.getElementById("selected-count");

function updateSelectedCount() {

    let checked =
        document.querySelectorAll(".item-checkbox:checked");

    countBox.textContent =
        "Wybrano: " + checked.length;
}

document.querySelectorAll(".item-checkbox")
.forEach(cb => {

    cb.addEventListener(
        "change",
        updateSelectedCount
    );

});

selectAll?.addEventListener("change", function() {

    document.querySelectorAll(".item-checkbox")
    .forEach(cb => {

        cb.checked = this.checked;

    });

    updateSelectedCount();
});

// ===========================
// MENU KONTEKSTOWE
// ===========================

const contextMenu = document.getElementById("context-menu");

let currentItem = "";

document.querySelectorAll(".file-row").forEach(row => {

    row.addEventListener("contextmenu", function(e) {

        e.preventDefault();

        currentItem = row.dataset.name;

        contextMenu.style.left = e.pageX + "px";
        contextMenu.style.top = e.pageY + "px";

        contextMenu.classList.remove("hidden");

    });

});

// =====================================
// MENU KONTEKSTOWE - ZIP
// =====================================

document.getElementById("ctx-zip").onclick = function() {

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/bulk_zip";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    let itemsInput = document.createElement("input");
    itemsInput.type = "hidden";
    itemsInput.name = "items";
    itemsInput.value = JSON.stringify([currentItem]);

    form.appendChild(pathInput);
    form.appendChild(itemsInput);

    document.body.appendChild(form);
    form.submit();

};


// =====================================
// MENU KONTEKSTOWE - UDOSTĘPNIJ
// =====================================

document.getElementById("ctx-share").onclick = function() {

    window.location =
        "/share_create?path={{ current_path }}&name=" +
        encodeURIComponent(currentItem);

};


// =====================================
// MENU KONTEKSTOWE - KOPIUJ
// =====================================

document.getElementById("ctx-copy").onclick = function() {

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/clipboard_copy";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    let itemsInput = document.createElement("input");
    itemsInput.type = "hidden";
    itemsInput.name = "items";
    itemsInput.value = JSON.stringify([currentItem]);

    form.appendChild(pathInput);
    form.appendChild(itemsInput);

    fetch("/clipboard_copy", {
        method: "POST",
        body: new FormData(form)
    });

    alert("Skopiowano do schowka.");

};


// =====================================
// MENU KONTEKSTOWE - WKLEJ
// =====================================

document.getElementById("ctx-paste").onclick = function() {

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/clipboard_paste";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    form.appendChild(pathInput);

    document.body.appendChild(form);
    form.submit();

};


// =====================================
// MENU KONTEKSTOWE - PRZENIEŚ
// =====================================

document.getElementById("ctx-move").onclick = function() {

    moveItem(currentItem);

};


// =====================================
// MENU KONTEKSTOWE - ZMIEŃ NAZWĘ
// =====================================

document.getElementById("ctx-rename").onclick = function() {

    renameItem(currentItem);

};


// =====================================
// MENU KONTEKSTOWE - WERSJE
// =====================================

document.getElementById("ctx-versions").onclick = function() {

    window.location =
        "/versions?name=" +
        encodeURIComponent(currentItem);

};


// =====================================
// MENU KONTEKSTOWE - USUŃ
// =====================================

document.getElementById("ctx-delete").onclick = function() {

    if (!confirm("Usunąć element?"))
        return;

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/bulk_delete";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    let itemsInput = document.createElement("input");
    itemsInput.type = "hidden";
    itemsInput.name = "items";
    itemsInput.value = JSON.stringify([currentItem]);

    form.appendChild(pathInput);
    form.appendChild(itemsInput);

    document.body.appendChild(form);
    form.submit();

};

// MENU KONTEKSTOWE - POBIERZ
// =====================================

document.getElementById("ctx-download").onclick = function () {

    alert(window.currentPath);

    window.location =
        "/download?path=" +
        encodeURIComponent(window.currentPath || "") +
        "&name=" +
        encodeURIComponent(currentItem);
};

// =====================================
// ZAMKNIĘCIE MENU PO KLIKNIĘCIU POZA NIM
// =====================================

document.addEventListener("click", function(e) {

    if (!contextMenu.contains(e.target)) {
        contextMenu.classList.add("hidden");
    }

});

function runBulkAction() {

    let action =
        document.getElementById("bulk-action").value;

    alert("ACTION = " + action);

    let selected = [];

    document.querySelectorAll(".item-checkbox:checked")
    .forEach(cb => {

        selected.push(cb.dataset.name);

    });
    
    if (action === "paste") {

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/clipboard_paste";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    form.appendChild(pathInput);

    document.body.appendChild(form);
    alert(form.action);
    form.submit();

    return;
}

    if (selected.length === 0) {

        alert("Nie zaznaczono plików.");
        return;
    }

    if (action === "download") {

    if (selected.length > 1) {
        alert("Dla wielu plików użyj 'Pobierz ZIP'.");
        return;
    }

    window.location =
        "/download?path={{ current_path }}&name=" +
        encodeURIComponent(selected[0]);

    return;
}

    if (action === "share") {

    if (selected.length !== 1) {

        alert("Zaznacz dokładnie jeden plik.");
        return;
    }

    window.location =
        "/share_create?path={{ current_path }}&name=" +
        encodeURIComponent(selected[0]);

    return;
}

    if (action === "zip") {

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/bulk_zip";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    let itemsInput = document.createElement("input");
    itemsInput.type = "hidden";
    itemsInput.name = "items";
    itemsInput.value = JSON.stringify(selected);

    form.appendChild(pathInput);
    form.appendChild(itemsInput);

    document.body.appendChild(form);
    document.body.appendChild(form);
    form.target = "_blank";
    form.submit();

    return;
}

    if (action === "delete") {

        if (!confirm(
            "Usunąć zaznaczone elementy?"
        )) {
            return;
        }

        let form = document.createElement("form");

        form.method = "POST";
        form.action = "/bulk_delete";

        let pathInput = document.createElement("input");
        pathInput.type = "hidden";
        pathInput.name = "current_path";
        pathInput.value = "{{ current_path }}";

        let itemsInput = document.createElement("input");
        itemsInput.type = "hidden";
        itemsInput.name = "items";
        itemsInput.value = JSON.stringify(selected);

        form.appendChild(pathInput);
        form.appendChild(itemsInput);

        document.body.appendChild(form);
        form.submit();

        return;
    }

    if (action === "clipboard_copy") {
    
    let form = document.createElement("form");

form.method = "POST";
form.action = "/clipboard_copy";

let pathInput = document.createElement("input");
pathInput.type = "hidden";
pathInput.name = "current_path";
pathInput.value = "{{ current_path }}";

let itemsInput = document.createElement("input");
itemsInput.type = "hidden";
itemsInput.name = "items";
itemsInput.value = JSON.stringify(selected);

form.appendChild(pathInput);
form.appendChild(itemsInput);

document.body.appendChild(form);

fetch("/clipboard_copy", {
    method: "POST",
    body: new FormData(form)
});

alert("Skopiowano do schowka.");

return;

}

   if (action === "copy") {

    let targetFolder = prompt(
        "Podaj folder docelowy:"
    );

    if (!targetFolder)
        return;

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/bulk_copy";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    let itemsInput = document.createElement("input");
    itemsInput.type = "hidden";
    itemsInput.name = "items";
    itemsInput.value = JSON.stringify(selected);

    let targetInput = document.createElement("input");
    targetInput.type = "hidden";
    targetInput.name = "target_folder";
    targetInput.value = targetFolder;

    form.appendChild(pathInput);
    form.appendChild(itemsInput);
    form.appendChild(targetInput);

    document.body.appendChild(form);
    form.submit();

    return;
}

    if (action === "move") {

    let targetFolder = prompt(
        "Podaj folder docelowy:"
    );

    if (!targetFolder)
        return;

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/bulk_move";

    let pathInput = document.createElement("input");
    pathInput.type = "hidden";
    pathInput.name = "current_path";
    pathInput.value = "{{ current_path }}";

    let itemsInput = document.createElement("input");
    itemsInput.type = "hidden";
    itemsInput.name = "items";
    itemsInput.value = JSON.stringify(selected);

    let targetInput = document.createElement("input");
    targetInput.type = "hidden";
    targetInput.name = "target_folder";
    targetInput.value = targetFolder;

    form.appendChild(pathInput);
    form.appendChild(itemsInput);
    form.appendChild(targetInput);

    document.body.appendChild(form);
    form.submit();

    return;
}

    alert("Ta akcja nie jest jeszcze gotowa.");
}

function copyItem(itemName) {

    let targetFolder = prompt(
        "Podaj folder docelowy (np. Dokumenty lub Faktury/2026):"
    );

    if (!targetFolder)
        return;

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/copy";

    form.innerHTML = `
        <input type="hidden" name="current_path" value="{{ current_path }}">
        <input type="hidden" name="item_name" value="${itemName}">
        <input type="hidden" name="target_folder" value="${targetFolder}">
    `;

    document.body.appendChild(form);
    form.submit();
}

function moveItem(itemName) {

    let targetFolder = prompt(
        "Podaj folder docelowy (np. Dokumenty lub Faktury/2026):"
    );

    if (!targetFolder)
        return;

    let form = document.createElement("form");

    form.method = "POST";
    form.action = "/move";

    form.innerHTML = `
        <input type="hidden" name="current_path" value="{{ current_path }}">
        <input type="hidden" name="item_name" value="${itemName}">
        <input type="hidden" name="target_folder" value="${targetFolder}">
    `;

    document.body.appendChild(form);
    form.submit();
}


});
