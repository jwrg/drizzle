// document.getElementById("time").addEventListener("input", () => {
//   setBubble(document.getElementById("time"),document.getElementById("time").nextElementSibling);
// });
// setBubble(document.getElementById("time"),document.getElementById("time").nextElementSibling);

function setBubble(range, bubble) {
  const val = range.value;
  const min = range.min ? range.min : 0;
  const max = range.max ? range.max : 100;
  const newVal = Number(((val - min) * 100) / (max - min));
  bubble.innerHTML = val == 1 ? val + '&nbsp;minute' : val + '&nbsp;minutes';
  bubble.style.left = `calc(${newVal}% + (${8 - newVal * 0.15}px))`;
}

function get_seconds(time_string) {
  let time_array = time_string.split(':').map(x => Number(x));
  if (time_array.length === 2) {
    time_array[0] = time_array[0] * 60;
  } else {
    time_array[0] = time_array[0] * 3600;
    time_array[1] = time_array[1] * 60;
  }
  return time_array.reduce((acc, curr) => acc + curr, 0);
}

function format_seconds(remaining) {
  const seconds = remaining % 60 < 10 ? '0' + Math.floor(remaining % 60).toString() : Math.floor(remaining % 60).toString();
  const minutes = (remaining / 60) % 60 < 10 ? '0' + Math.floor((remaining / 60) % 60).toString() : Math.floor((remaining / 60) % 60).toString();
  const hours = Math.floor(remaining / 3600).toString();
  return hours === '0' ? minutes + ':' + seconds : hours + ':' + minutes + ':' + seconds;
}

function set_countdown(el) {
  el.value = format_seconds(el.value);
  return setInterval(function() {
    seconds = get_seconds(el.value);
    if (seconds <= 0 || seconds === NaN) {
      window.location.reload();
    } else {
      el.value = format_seconds(seconds - 1);
    }
  }, 1000);
}

function set_countup(el) {
  var current = new Date();
  el.innerHTML = current.toLocaleString();
  return setInterval(function() {
    current.setSeconds(current.getSeconds() + 1);
    el.innerHTML = current.toLocaleString();
  }, 1000);
}

const active_buttons = Array.from(document.getElementsByClassName('active'));
var datetime = set_countup(document.getElementById('datetime'));
let handles = [];
for (let i = 0; i < active_buttons.length; ++i) {
  handles[i] = set_countdown(active_buttons[i]);
}
