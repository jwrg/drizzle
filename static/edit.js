function change_id_number(string, increment = true) {
  let array = string.split('-');
  let tail = Number(array.pop());
  if (increment) {
    array.push(String(++tail));
  } else {
    array.push(String(--tail));
  }
  return array.join('-');
}

function change_row_numbers(row, increment = true) {
  for (let el of row.children) {
    if (el.firstElementChild.tagName != "A") {
      el.firstElementChild.htmlFor = change_id_number(el.firstElementChild.htmlFor, increment);
      el.lastElementChild.id = change_id_number(el.lastElementChild.id, increment);
      el.lastElementChild.name = change_id_number(el.lastElementChild.name, increment);
    } else if (el.firstElementChild.tagName == "A") {
      for (let child of el.children) {
        child.id = change_id_number(child.id, increment);
      }
    }
  }
}

function change_number(string, increment = true, index = 1, delimiter = '-') {
  let array = string.split(delimiter);
  let operand = Number(array[index]);
  array[index] = increment ? ++operand : --operand;
  return array.join(delimiter);
}

function change_row_indices(row, increment = true) {
  for (
    let target of [
      {'selector': 'table', 'attribute': 'id'},
      {'selector': 'tr th label', 'attribute': 'for'},
      {'selector': 'td select', 'attribute': 'id'},
      {'selector': 'td select', 'attribute': 'name'},
      {'selector': 'tr td input', 'attribute': 'id'},
      {'selector': 'tr td input', 'attribute': 'name'}
    ]
  ) {
    for (let element of row.querySelectorAll(target['selector'])) {
      element.setAttribute(target['attribute'], change_number(element.getAttribute(target['attribute']), increment=increment));
    }
  } 
}

function append_row() {
  const form = document.querySelector('form dl');
  const old_row = document.querySelector('dl dd table').parentElement.parentElement.lastElementChild;
  let new_row = old_row.cloneNode(true);
  change_row_indices(new_row);
  if (new_row.querySelector('tr td select') !== null){
    new_row.querySelector('tr td select').value = new_row.querySelector('tr td select').options[0].value;
  }
  form.insertBefore(new_row, null);
}

function delete_row(button) {
  const row = button.parentElement;
  let next_row = row.nextElementSibling;
  if (row.previousElementSibling.tagName == "DD" || row.nextElementSibling) {
    row.remove();
    while (next_row) {
      change_row_indices(next_row, false);
      next_row = next_row.nextElementSibling;
    };
  } else {
    row.querySelector('tr td select').value = row.querySelector('tr td select').options[0].value;
  }
}

function swap_row(new_precedent, new_successor) {
  if (new_successor !== null) change_row_indices(new_successor);
  if (new_precedent !== null) change_row_indices(new_precedent, false);
  new_successor.parentElement.insertBefore(new_precedent, new_successor);
}

function demote_row(button) {
  if (button.parentElement.previousElementSibling.tagName == "DD") swap_row(button.parentElement, button.parentElement.previousElementSibling);
}

function promote_row(button) {
  if (button.parentElement.nextElementSibling) swap_row(button.parentElement.nextElementSibling, button.parentElement)
}

function validate_form() {
  let indices = [];
  document.querySelectorAll("table tr td select").forEach(el => indices.push(el.selectedIndex));
  if (indices.length > new Set(indices).size) {
    alert("Dependency list must not contain duplicate relays.")
    return false;
  }
  else return true;
}
