function increment_id_number(string) {
  let array = string.split('-');
  let tail = Number(array.pop());
  array.push(String(++tail));
  return array.join('-');
}

function append_row() {
  const table = document.getElementById("sequence-table");
  const old_row = table.lastElementChild.lastElementChild;
  let new_row = old_row.cloneNode(true);
  let new_select = new_row.firstElementChild.firstElementChild;
  new_select.id = increment_id_number(new_select.id);
  let new_number = new_row.firstElementChild.nextElementSibling.firstElementChild;
  new_number.id = increment_id_number(new_number.id);
  table.lastElementChild.appendChild(new_row);
}

function delete_row(el) {
  if (el.parentElement.parentElement.parentElement.children.length > 2) el.parentElement.parentElement.remove();
}
