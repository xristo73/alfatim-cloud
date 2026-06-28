// =====================================
// MODAL WYBORU FOLDERU
// =====================================

const folderModal = document.getElementById("folder-modal");
const folderCancel = document.getElementById("folder-cancel");
const folderOk = document.getElementById("folder-ok");

let folderCallback = null;
let selectedFolder = "";

async function openFolderModal(callback) {

    folderCallback = callback;
    selectedFolder = "";

    folderModal.classList.remove("hidden");

    let response = await fetch("/folders");
    let folders = await response.json();

    let list = document.getElementById("folder-list");

    list.innerHTML = "";

    folders.forEach(folder => {

        let div = document.createElement("div");

        div.className =
            "p-2 border-b cursor-pointer hover:bg-gray-100";

        div.textContent =
            folder === "" ? "/" : folder;

        div.onclick = function () {

            document.querySelectorAll("#folder-list div")
                .forEach(d => d.classList.remove("bg-blue-200"));

            div.classList.add("bg-blue-200");

            selectedFolder = folder;

        };

        list.appendChild(div);

    });

}

function closeFolderModal() {

    folderModal.classList.add("hidden");

}

folderCancel.onclick = function () {

    closeFolderModal();

};

folderOk.onclick = function () {

    if (!selectedFolder)
        return;

    closeFolderModal();

    if (folderCallback) {
        folderCallback(selectedFolder);
    }

};
