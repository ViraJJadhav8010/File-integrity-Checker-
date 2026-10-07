/**
 * File Integrity Checker - Frontend Interactive Scripts
 */

document.addEventListener("DOMContentLoaded", function () {
    // ---------------------------------------------------------
    // Password Show/Hide Toggle
    // ---------------------------------------------------------
    document.querySelectorAll(".btn-toggle-password").forEach(function (button) {
        button.addEventListener("click", function () {
            const targetId = this.getAttribute("data-target");
            const targetInput = document.getElementById(targetId);
            const icon = this.querySelector("i");

            if (targetInput) {
                if (targetInput.type === "password") {
                    targetInput.type = "text";
                    if (icon) {
                        icon.classList.remove("fa-eye");
                        icon.classList.add("fa-eye-slash");
                    }
                } else {
                    targetInput.type = "password";
                    if (icon) {
                        icon.classList.remove("fa-eye-slash");
                        icon.classList.add("fa-eye");
                    }
                }
            }
        });
    });

    // ---------------------------------------------------------
    // Drag & Drop File Upload Zones
    // ---------------------------------------------------------
    const dropzone = document.getElementById("fileDropzone");
    const fileInput = document.getElementById("fileInput");
    const dropzoneText = document.getElementById("dropzoneText");

    if (dropzone && fileInput) {
        dropzone.addEventListener("click", function () {
            fileInput.click();
        });

        ["dragenter", "dragover"].forEach(eventName => {
            dropzone.addEventListener(eventName, function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add("dragover");
            }, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropzone.addEventListener(eventName, function (e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove("dragover");
            }, false);
        });

        dropzone.addEventListener("drop", function (e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateDropzoneDisplay(files[0].name);
            }
        });

        fileInput.addEventListener("change", function () {
            if (this.files.length > 0) {
                updateDropzoneDisplay(this.files[0].name);
            }
        });

        function updateDropzoneDisplay(fileName) {
            if (dropzoneText) {
                dropzoneText.innerHTML = `Selected: <strong class="text-cyan">${fileName}</strong>`;
            }
            const autoSubmitForm = dropzone.getAttribute("data-auto-submit");
            if (autoSubmitForm) {
                document.getElementById(autoSubmitForm).submit();
            }
        }
    }

    // ---------------------------------------------------------
    // Copy Hash to Clipboard
    // ---------------------------------------------------------
    document.querySelectorAll(".btn-copy-hash").forEach(function (button) {
        button.addEventListener("click", function () {
            const hashText = this.getAttribute("data-hash");
            if (hashText) {
                navigator.clipboard.writeText(hashText).then(() => {
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="fa-solid fa-check text-success"></i> Copied!';
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                }).catch(err => {
                    console.error("Clipboard copy failed:", err);
                });
            }
        });
    });

    // ---------------------------------------------------------
    // Instant Live Table Filtering
    // ---------------------------------------------------------
    const liveSearchInput = document.getElementById("tableLiveSearch");
    if (liveSearchInput) {
        liveSearchInput.addEventListener("keyup", function () {
            const filterValue = this.value.toLowerCase();
            const tableRows = document.querySelectorAll(".filterable-table tbody tr");

            tableRows.forEach(row => {
                const textContent = row.textContent.toLowerCase();
                if (textContent.includes(filterValue)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    // ---------------------------------------------------------
    // Asynchronous Baseline Deletion
    // ---------------------------------------------------------
    document.querySelectorAll(".btn-delete-baseline").forEach(function (button) {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            const fileId = this.getAttribute("data-id");
            const fileName = this.getAttribute("data-name");

            if (confirm(`Are you sure you want to delete the baseline hash for "${fileName}"? This cannot be undone.`)) {
                fetch(`/api/delete-baseline/${fileId}`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    }
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const targetRow = document.getElementById(`row-file-${fileId}`);
                        if (targetRow) {
                            targetRow.remove();
                        }
                        // Refresh stat count if available
                        const totalCountEl = document.getElementById("statTotalFiles");
                        if (totalCountEl) {
                            let curr = parseInt(totalCountEl.innerText) || 1;
                            totalCountEl.innerText = Math.max(0, curr - 1);
                        }
                    } else {
                        alert(data.message || "Failed to delete baseline.");
                    }
                })
                .catch(err => {
                    console.error("Delete request error:", err);
                    alert("Network error deleting baseline.");
                });
            }
        });
    });

    // ---------------------------------------------------------
    // Auto-dismiss Alerts after 5 seconds
    // ---------------------------------------------------------
    setTimeout(function () {
        document.querySelectorAll(".alert-auto-dismiss").forEach(alert => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        });
    }, 5000);
});
