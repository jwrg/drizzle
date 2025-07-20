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

function append_row() {
  const table = document.querySelector('form table');
  const old_row = table.lastElementChild.lastElementChild;
  let new_row = old_row.cloneNode(true);
  change_row_numbers(new_row);
  table.lastElementChild.appendChild(new_row);
}

function delete_row(button) {
  let row = button.parentElement.parentElement;
  // TODO!!! :
  // decrement all rows that succeed the deleted row
  if (row.parentElement.children.length > 2) row.remove();
}

function demote_row(button) {
  let successor = button.parentElement.parentElement;
  let precedent = button.parentElement.parentElement.nextElementSibling;
  change_row_numbers(successor);
  change_row_numbers(precedent, false);
  successor.parentElement.insertBefore(successor, successor.nextElementSibling.nextElementSibling);
}

function promote_row(button) {
  let successor = button.parentElement.parentElement.previousElementSibling;
  let precedent = button.parentElement.parentElement;
  change_row_numbers(successor);
  change_row_numbers(precedent, false);
  successor.parentElement.insertBefore(successor, successor.nextElementSibling.nextElementSibling);
}
