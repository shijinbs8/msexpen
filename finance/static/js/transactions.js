/**
 * Transactions JavaScript Helpers & Dynamic Category Filter
 */

document.addEventListener('DOMContentLoaded', function () {
    const typeToggleExpense = document.getElementById('toggleExpense');
    const typeToggleIncome = document.getElementById('toggleIncome');
    const hiddenTypeInput = document.getElementById('id_transaction_type');
    
    // Select inputs (both Quick Add modal select & main form select)
    const categorySelects = [
        document.getElementById('id_category'),
        document.getElementById('quick_add_category')
    ].filter(el => el !== null);

    function filterCategoriesByType(selectedType) {
        categorySelects.forEach(select => {
            let firstMatchedVal = '';
            let hasSelectedCurrent = false;

            Array.from(select.options).forEach(opt => {
                if (opt.value === '') {
                    opt.hidden = false;
                    return;
                }
                const catType = opt.getAttribute('data-type');
                if (!catType || catType === selectedType) {
                    opt.hidden = false;
                    opt.disabled = false;
                    if (!firstMatchedVal) firstMatchedVal = opt.value;
                    if (opt.selected) hasSelectedCurrent = true;
                } else {
                    opt.hidden = true;
                    opt.disabled = true;
                    if (opt.selected) opt.selected = false;
                }
            });

            // If current selection was hidden or empty, auto select first matched
            if (!hasSelectedCurrent && firstMatchedVal) {
                select.value = firstMatchedVal;
            }
        });
    }

    if (typeToggleExpense && typeToggleIncome && hiddenTypeInput) {
        typeToggleExpense.addEventListener('click', function () {
            typeToggleExpense.classList.add('active-expense');
            typeToggleIncome.classList.remove('active-income');
            hiddenTypeInput.value = 'EXPENSE';
            filterCategoriesByType('EXPENSE');
        });

        typeToggleIncome.addEventListener('click', function () {
            typeToggleIncome.classList.add('active-income');
            typeToggleExpense.classList.remove('active-expense');
            hiddenTypeInput.value = 'INCOME';
            filterCategoriesByType('INCOME');
        });

        // Initialize category filter based on initial hidden type value
        const initialType = hiddenTypeInput.value || 'EXPENSE';
        filterCategoriesByType(initialType);
    } else {
        // Fallback initial filter if toggles aren't on page
        filterCategoriesByType('EXPENSE');
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
                    const modalEl = document.getElementById('quickAddModal');
                    const modalInstance = bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) modalInstance.hide();
                    window.location.reload();
                } else {
                    alert("Error saving transaction: " + (data.message || "Please select a valid category and amount."));
                }
            })
            .catch(err => {
                console.error("Quick add error:", err);
                alert("Network error. Please try again.");
            });
        });
    }
});
