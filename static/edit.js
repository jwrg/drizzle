function increment_id_number(string) {
  let array = string.split('-');
  let tail = Number(array.pop());
  array.push(String(++tail));
  return array.join('-');
}

function append_row() {
  const table = document.querySelector('form table');
  const old_row = table.lastElementChild.lastElementChild;
  let new_row = old_row.cloneNode(true);
  for (let el of new_row.children) {
    if (el.firstElementChild.tagName != "A") {
      el.firstElementChild.htmlFor = increment_id_number(el.firstElementChild.htmlFor);
      el.lastElementChild.id = increment_id_number(el.lastElementChild.id);
      el.lastElementChild.name = increment_id_number(el.lastElementChild.name);
    }
  }
  table.lastElementChild.appendChild(new_row);
}

function delete_row(el) {
  if (el.parentElement.parentElement.parentElement.children.length > 2) el.parentElement.parentElement.remove();
}
