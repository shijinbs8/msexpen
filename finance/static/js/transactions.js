/**
 * Transactions JavaScript Helpers
 */

document.addEventListener('DOMContentLoaded', function () {
    // Expense vs Income Type Toggle in Add Form
    const typeToggleExpense = document.getElementById('toggleExpense');
    const typeToggleIncome = document.getElementById('toggleIncome');
    const hiddenTypeInput = document.getElementById('id_transaction_type');
    const categorySelect = document.getElementById('id_category');

    function updateCategoryDropdown(selectedType) {
        if (!categorySelect) return;
        const options = categorySelect.options;
        for (let i = 0; i < options.length; i++) {
            const opt = options[i];
            const text = opt.text.toLowerCase();
            // Optional dynamic filtering if options have attributes or text indicators
        }
    }

    if (typeToggleExpense && typeToggleIncome && hiddenTypeInput) {
        typeToggleExpense.addEventListener('click', function () {
            typeToggleExpense.classList.add('active-expense');
            typeToggleIncome.classList.remove('active-income');
            hiddenTypeInput.value = 'EXPENSE';
            updateCategoryDropdown('EXPENSE');
        });

        typeToggleIncome.addEventListener('click', function () {
            typeToggleIncome.classList.add('active-income');
            typeToggleExpense.classList.remove('active-expense');
            hiddenTypeInput.value = 'INCOME';
            updateCategoryDropdown('INCOME');
        });
    }

    // Quick Add Modal Form AJAX Handler
    const quickAddForm = document.getElementById('quickAddForm');
    if (quickAddForm) {
        quickAddForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(quickAddForm);

            fetch('/transactions/quick-add/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Close modal and reload page
                    const modalEl = document.getElementById('quickAddModal');
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) modalInstance.hide();
                    window.location.reload();
                } else {
                    alert("Error saving transaction: " + (data.message || "Please check inputs"));
                }
            })
            .catch(err => {
                console.error("Quick add error:", err);
                alert("Network error. Please try again.");
            });
        });
    }
});
